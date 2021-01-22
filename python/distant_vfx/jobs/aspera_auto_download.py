import os
import re
import subprocess
import traceback
import yagmail
from ..aspera import AsperaCLI, AsperaError
from ..constants import PACKAGE_REGEX, MAILBOX_BASE_PATH, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_RECIPIENTS, \
    FASPEX_SUPE_USERNAME, HHM_INTERNAL_FASPEX_USERNAME, EG_INTERNAL_FASPEX_USERNAME
from . import new_vendor_package


def main(user,
         password,
         url,
         package_id_json_file,
         url_prefix,
         output_path,
         content_protect_password,
         vendor,
         catch_up_mode=False):

    aspera = AsperaCLI(
        user=user,
        password=password,
        url=url,
        package_id_json_file=package_id_json_file,
        url_prefix=url_prefix
    )

    # Catch up mode allows for updating to latest package id without downloading any packages.
    if catch_up_mode:
        latest_package_id = aspera.set_latest_package_id()
        subject = f'[DISTANT_API] Latest package ID updated for vendor {vendor}'
        content = f'Latest package ID has been updated to {latest_package_id}. Packages prior to this will not be ' \
                  f'auto downloaded.'
        _send_email(subject, content)
        return

    # Download new packages, updating package json file after each download
    packages = None
    try:
        print(f'Checking for new {vendor} packages...')
        packages = aspera.download_new_packages(
                output_path=output_path,
                content_protect_password=content_protect_password
            )
    except AsperaError as e:
        subject = f'[DISTANT_API] Error downloading package {e.package_title}'
        content = f'There was an error downloading package {e.package_title}. Please see below for details.\n\n' \
                  f'{traceback.format_exc()}'
        _send_email(subject, content)

    # Exit if there are no packages downloaded
    if not packages:
        print(f'No new packages found for vendor {vendor}.')
        return

    # Move downloaded packages to mailbox
    for (package, author) in packages:

        if author in FASPEX_SUPE_USERNAME:
            vendor_fmt = 'ldq'
        elif author in HHM_INTERNAL_FASPEX_USERNAME:
            vendor_fmt = 'hhm'
        elif author in EG_INTERNAL_FASPEX_USERNAME:
            vendor_fmt = 'eg'
        else:
            vendor_fmt = vendor

        # Get the base mailbox directory where the package should be sorted
        mailbox_dir = os.path.join(MAILBOX_BASE_PATH, vendor_fmt, f'fr_{vendor_fmt}')

        package_name = _get_package_name_strip(package)

        subject = f'[DISTANT_API] Downloaded package {package_name}'
        content = None

        # Check if the package has a valid package name
        sub_package_path = _get_sub_package_path(package)

        # If so, move the package to the proper mailbox folder if it does not exist already
        if sub_package_path:
            download_path = os.path.join(mailbox_dir, package_name)
            try:
                print(f'Moving package {package_name} to {mailbox_dir}...')
                _move_package(sub_package_path, mailbox_dir)
                print(f'Package {package_name} moved to {mailbox_dir}.')
            except FileExistsError:
                content = f'Error: Package {package_name} already exists at destination {download_path}. Package ' \
                          f'{package_name} will remain at manual sort path {output_path}.'

        # If not, create a new vendor package and move the contents there
        else:
            sort_path = new_vendor_package.main([vendor_fmt], incoming=True)[0]
            download_path = sort_path
            for item in os.listdir(package):
                item_path = os.path.join(package, item)
                print(f'Moving package {package_name} to {sort_path}...')
                _move_package(item_path, sort_path)
                print(f'Package {package_name} moved to {sort_path}.')

        # Remove the empty container folder 'PKG - {package_name}' from default download location
        if len(os.listdir(package)) == 0:
            print(f'Cleaning up empty package folder: {package}')
            os.rmdir(package)

        # Set the content message if not already set.
        if not content:
            content = f'Package {package_name} has been downloaded and moved to path: {download_path}.'

        # Send an email notification.
        _send_email(subject, content)


def _get_sub_package_path(package):
    package_name_strip = _get_package_name_strip(package)
    sub_package_path = None
    if _is_valid_package_name(package_name_strip):
        sub_package_path = os.path.join(package, package_name_strip)
    return sub_package_path


def _get_package_name_strip(package):
    package_name = os.path.basename(package)
    return package_name.replace('PKG - ', '')


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


def _is_valid_package_name(package_name):
    pattern = re.compile(PACKAGE_REGEX)
    match = re.match(pattern, package_name)
    if match:
        return True
    return False
