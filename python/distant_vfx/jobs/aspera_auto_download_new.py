import os
import re
import subprocess
import traceback
import yagmail

from ..constants import PACKAGE_REGEX, MAILBOX_BASE_PATH, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_RECIPIENTS
from ..aspera import AsperaCLI, AsperaError
from . import new_vendor_package


def main(host, data, catch_up_mode=False):

    aspera = AsperaCLI(
        user=data['user'],
        password=data['password'],
        url=data['base_url'],
        package_id_json_file=data['json_file'],
        url_prefix=data['prefix']
    )

    # Catch up mode allows for updating to latest package id without downloading any packages.
    if catch_up_mode:
        latest_package_id = aspera.set_latest_package_id()
        subject = f'[DISTANT_API] Latest package ID updated for faspex host: {host}'
        content = f'Latest package ID has been updated to {latest_package_id}. Packages prior to this will not be ' \
                  f'auto downloaded.'
        _send_email(subject, content)
        return

    # Download new packages, updating package json file after each download
    default_download_path = data['download_path']
    packages = None
    try:
        print(f'Checking for new {host} packages...')
        packages = aspera.download_new_packages(
                output_path=default_download_path,
                content_protect_password=data['content_protect_password']
            )
    except AsperaError as e:
        subject = f'[DISTANT_API] Error downloading package {e.package_title}'
        content = f'There was an error downloading package {e.package_title}. Please see below for details.\n\n' \
                  f'{traceback.format_exc()}'
        _send_email(subject, content)

    # Exit if there are no packages downloaded
    if not packages:
        print(f'No new packages found at host {host}.')
        return

    # Move downloaded packages to mailbox
    for (package, author) in packages:

        vendor = _get_vendor(author, data)
        if not vendor:
            subject = f'[DISTANT_API] Error: Could not match vendor to package {os.path.basename(package)}'
            content = f'Could not match a vendor to the package at path: {package}'
            _send_email(subject, content)
            continue

        mailbox_dir = os.path.join(MAILBOX_BASE_PATH, vendor, f'fr_{vendor}')
        os.makedirs(mailbox_dir, exist_ok=True)
        package_name = _get_package_name_strip(package)
        subject = f'[DISTANT_API] Downloaded package {package_name}'
        content = None

        # Check if the package has a valid package name
        sub_package_path = _get_sub_package_path(package, vendor)

        if sub_package_path:
            download_path = os.path.join(mailbox_dir, package_name)
            try:
                print(f'Moving package {package_name} to {mailbox_dir}...')
                _move_package(sub_package_path, mailbox_dir)
                print(f'Package {package_name} moved to {mailbox_dir}.')
            except FileExistsError:
                content = f'Error: Package {package_name} already exists at destination {download_path}. Package ' \
                          f'{package_name} will remain at manual sort path {default_download_path}.'

        elif _is_valid_package_name(package_name, vendor):
            download_path = os.path.join(mailbox_dir, package_name)
            try:
                print(f'Moving package {package_name} to {mailbox_dir}...')
                _move_package(package, download_path)
                print(f'Package {package_name} moved to {mailbox_dir}.')
            except FileExistsError:
                content = f'Error: Package {package_name} already exists at destination {download_path}. Package ' \
                          f'{package_name} will remain at manual sort path {default_download_path}.'

        # If not, create a new vendor package and move the contents there
        else:
            sort_path = new_vendor_package.main([vendor], incoming=True)[0]
            download_path = sort_path
            for item in os.listdir(package):
                item_path = os.path.join(package, item)
                print(f'Moving package {package_name} to {sort_path}...')
                _move_package(item_path, sort_path)
                print(f'Package {package_name} moved to {sort_path}.')

        # Remove the empty container folder 'PKG - {package_name}' from default download location
        try:
            if len(os.listdir(package)) == 0:
                print(f'Cleaning up empty package folder: {package}')
                os.rmdir(package)
        except FileNotFoundError:
            pass

        # Set the content message if not already set.
        if not content:
            content = f'Package {package_name} has been downloaded and moved to path: {download_path}.'

        # Send an email notification.
        _send_email(subject, content)


def _move_package(source, dest):
    cmd = ['mv', source, dest]
    dest_folder = os.path.basename(source)
    dest_path = os.path.join(dest, dest_folder)
    if os.path.exists(dest_path):
        raise FileExistsError
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=False
    )
    stdout, stderr = process.communicate()
    return stdout, stderr


def _get_sub_package_path(package, vendor_code):
    package_name_strip = _get_package_name_strip(package)
    if _is_valid_package_name(package_name_strip, vendor_code):
        sub_package_path = os.path.join(package, package_name_strip)
        if os.path.exists(sub_package_path):
            return sub_package_path
    return None


def _is_valid_package_name(package_name, vendor_code):
    pattern = re.compile(PACKAGE_REGEX)
    match = re.match(pattern, package_name)
    if match:
        split = match.group(0).split('_')
        try:
            vendor = split[1]
            return vendor.lower() in vendor_code.lower()
        except IndexError:
            return False
    return False


def _get_package_name_strip(package):
    package_name = os.path.basename(package)
    return package_name.replace('PKG - ', '')


def _get_vendor(author, aspera_data):
    vendors = aspera_data['vendors']
    for vendor, vendor_data in vendors.items():
        authors = vendor_data['authors']
        if author.lower() in [a.lower() for a in authors]:
            return vendor
    return None


def _send_email(subject, content):
    yag = yagmail.SMTP(
        user=EMAIL_USERNAME,
        password=EMAIL_PASSWORD
    )
    yag.send(
        to=EMAIL_RECIPIENTS.split(','),
        subject=subject,
        contents=content
    )