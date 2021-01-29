import json
import os
import subprocess
import traceback
import sys
from html import unescape
from operator import itemgetter
from bs4 import BeautifulSoup


class AsperaError(Exception):

    def __init__(self, message, package_title):
        self.message = message
        self.package_title = package_title


class AsperaCLI:

    def __init__(self, user, password, url, package_id_json_file, url_prefix='aspera/faspex'):
        self.user = user
        self.password = password
        self.url = url
        self.package_id_json_file = package_id_json_file
        self.url_prefix = url_prefix

    def set_latest_package_id(self):
        # write the latest package ID to provided .json file
        inbox_packages = self._fetch_inbox_packages()
        if inbox_packages:
            max_package_id = self._get_max_package_id_from_list(inbox_packages)
            self._write_last_processed_package_id_file(max_package_id, self.package_id_json_file)
            return max_package_id
        return None

    def send_package(self, filepath, recipients, title,
                     note=None, content_protect_password=None, cc_on_download=None, cc_on_upload=None):

        # validate the input params
        if not os.path.exists(filepath):
            raise FileNotFoundError(f'Path does not exist: {filepath}')
        elif not recipients:
            raise ValueError(f'You must provide a valid list of recipients')
        elif not title:
            raise ValueError(f'You must provide a title')

        flags = ['--file', filepath, '--title', title]

        # add recipients, cc recipients, & note
        for recipient in recipients:
            recipient_flag = ['--recipient', recipient]
            flags += recipient_flag

        if cc_on_download:
            for cc in cc_on_download:
                flags += ['--cc-on-download', cc]

        if cc_on_upload:
            for cc in cc_on_upload:
                flags += ['--cc-on-upload', cc]

        if note:
            flags += ['--note', note]

        # set password
        if content_protect_password:
            self._set_file_pass(content_protect_password)
            flags.append('--file-encrypt')

        # send the package
        cmd = self._construct_cmd('send', flags=flags)
        self._call_aspera_cli(cmd)

    @staticmethod
    def _set_file_pass(password):
        # set the content-protect password
        from os import environ
        environ['ASPERA_SCP_FILEPASS'] = str(password)

    def download_package_by_name(self, package_name, output_path, content_protect_password=None, inbox_packages=None):
        # download a single package by its title
        if not inbox_packages:
            inbox_packages = self._fetch_inbox_packages()
        link, author = None, None
        for package in inbox_packages:
            package_id, title, link_raw, author_raw, completed = package
            if not completed:
                print(f'Package {package_name} has not finished uploading.')
                sys.exit()
            if package_name in title:
                # grab the link if we have a title match
                link = link_raw
                author = author_raw
                break

        # if the package is found, try to download it
        if link:
            try:
                self._download_package(link, output_path, content_protect_password=content_protect_password)
                package_path = os.path.join(output_path, f'PKG - {package_name}')
                return package_path, author
            except:
                raise AsperaError(f'Error downloading package (title: {package_name})', package_name)
        else:
            raise AsperaError(f'No package found with name {package_name}', package_name)

    def download_new_packages(self, output_path, content_protect_password=None):
        # Download all new packages in the inbox

        # Get the last processed package ID from file for comparison
        last_processed_package_id = self._get_last_processed_package_id_from_file(self.package_id_json_file)
        try:
            inbox_packages = self._fetch_inbox_packages()

        # exit if no inbox packages are found or there is an error
        except:
            return None
        if not inbox_packages:
            return None

        # if there is no package ID for comparison, do NOT download any packages, just update the .json file
        if not last_processed_package_id:
            max_package_id = self._get_max_package_id_from_list(inbox_packages)
            self._write_last_processed_package_id_file(max_package_id, self.package_id_json_file)
            return None

        # otherwise, get a list of new packages
        new_packages = self._filter_new_packages(inbox_packages, last_processed_package_id)

        # sort by package id smallest -> greatest
        new_packages.sort(key=itemgetter(0))

        # download packages
        output_packages = []
        for package in new_packages:
            package_id, title, link, author, completed = package
            if not completed:
                print(f'Package {title} has not finished uploading. Will resume at this package once upload is complete.')
                break
            else:
                try:
                    print(f'Downloading package {title}...')
                    self._download_package(
                        link=link,
                        output_path=output_path,
                        content_protect_password=content_protect_password
                    )
                    print(f'Finished downloading package {title}.')
                    print(f'Updating package ID to {package_id}...')
                    self._write_last_processed_package_id_file(package_id, self.package_id_json_file)
                    package_name = f'PKG - {title}'
                    package_path = os.path.join(output_path, package_name)
                    output_packages.append((package_path, author))
                except:
                    traceback.print_exc()
                    raise AsperaError(f'Error downloading package (title: {title})', title)
        return output_packages

    def _download_package(self, link, output_path, content_protect_password=None):
        # Download one package from the provided link
        flags = ['--file', output_path, '--url', link]
        if content_protect_password:
            flags += ['--content-protect-password', content_protect_password]
        cmd = self._construct_cmd(sub_cmd='get', flags=flags)
        return self._call_aspera_cli(cmd)

    @staticmethod
    def _filter_new_packages(inbox_packages, last_processed_package_id):
        # Filter inbox package list to include only new packages which have not been processed yet
        new_packages = [package for package in inbox_packages if package[0] > last_processed_package_id]
        return new_packages

    @staticmethod
    def _get_max_package_id_from_list(inbox_packages):
        # Get the latest package ID from the inbox packages list
        packages_ids = [package[0] for package in inbox_packages]
        max_package_id = max(packages_ids)
        return max_package_id

    @staticmethod
    def _write_last_processed_package_id_file(last_processed_package_id, json_file):
        # Write the ID number of the last processed package to the provided .json file for later reference
        json_dict = {
            'id': last_processed_package_id
        }
        if last_processed_package_id is None:
            raise ValueError('Last processed package id cannot be None')
        with open(json_file, 'w') as file:
            json.dump(json_dict, file)

    @staticmethod
    def _get_last_processed_package_id_from_file(json_file):
        # Read the ID number of the last processed package from the provided .json file
        last_processed_package_id = None
        try:
            with open(json_file, 'r') as file:
                data = json.load(file)
                last_processed_package_id = data.get('id')
        except FileNotFoundError:
            traceback.print_exc()
        finally:
            return last_processed_package_id

    def _fetch_inbox_packages(self):
        # Get a list of packages in the "inbox" mailbox (these are the ones we want to download)
        return self._fetch_packages(mailbox='inbox')

    def _fetch_packages(self, mailbox):
        # Get a list of the latest packages from a given mailbox
        if mailbox not in ['inbox', 'sent', 'archived']:
            raise ValueError('mailbox must be either inbox, sent, or archived')
        mailbox_flag = '--' + mailbox
        flags = ['--xml', mailbox_flag]
        cmd = self._construct_cmd(sub_cmd='list', flags=flags)
        response, errors = self._call_aspera_cli(cmd)
        return self._parse_xml_response(response)

    @staticmethod
    def _parse_xml_response(xml):
        # Parse the xml package data returned by the faspex list call to get the download link, etc.
        packages = []
        xml = xml[xml.index('<'):]
        soup = BeautifulSoup(xml, 'xml')
        entries = soup.find_all('entry')
        if not entries:
            return None
        for entry in entries:
            delivery_id = int(entry.findChild('package:delivery_id').get_text())
            title = entry.findChild('title').get_text()
            link = unescape(entry.findChild('link', {'rel': 'package'})['href'])
            author = entry.findChild('author').findChild('name').get_text()
            completed = entry.findChild('completed').get_text()
            package = (delivery_id, title, link, author, completed)
            packages.append(package)
        return packages

    def _construct_cmd(self, sub_cmd, flags=None):
        # Build an aspera faspex command using all the necessary parameters
        cmd = ['aspera', 'faspex', sub_cmd]
        std_flags = ['--host', self.url, '--username', self.user, '--password', self.password, '-U', self.url_prefix]
        cmd += std_flags
        if flags:
            cmd += flags
        cmd = [str(i) for i in cmd]
        return cmd

    @staticmethod
    def _call_aspera_cli(cmd):
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=False
        )
        try:
            stdout, stderr = process.communicate()
            return stdout, stderr
        except:
            traceback.print_exc()
