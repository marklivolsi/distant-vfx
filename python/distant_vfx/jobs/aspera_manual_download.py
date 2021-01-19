import os
import re
import subprocess
import traceback
from ..aspera import AsperaCLI
from ..constants import PACKAGE_REGEX, MAILBOX_BASE_PATH
from . import new_vendor_package


def main(user,
         password,
         url,
         package_id_json_file,
         url_prefix,
         output_path,
         content_protect_password,
         package_name,
         vendor):

    aspera = AsperaCLI(
        user=user,
        password=password,
        url=url,
        package_id_json_file=package_id_json_file,
        url_prefix=url_prefix
    )

    # Download the package
    package = None
    try:
        package = aspera.download_package_by_name(
            package_name=package_name,
            output_path=output_path,
            content_protect_password=content_protect_password
        )
    except:
        traceback.print_exc()

    # Exit if no package is found with a matching title
    if not package:
        print(f'No package found with title {package_name}')
        return

    # Get the base mailbox directory where the package should be sorted
    mailbox_dir = os.path.join(MAILBOX_BASE_PATH, vendor, f'fr_{vendor}')

    # Check if the package has a valid package name
    sub_package_path = _get_sub_package_path(package)

    # If so, move the package to the proper mailbox folder if it does not exist already
    if sub_package_path:
        download_path = os.path.join(mailbox_dir, _get_package_name_strip(package))
        print(f'Moving package to path: {download_path}')
        try:
            _move_package(sub_package_path, mailbox_dir)
        except FileExistsError:
            print(f'Package already exists at destination: {download_path}\n'
                  f'File will remain at default download path: {output_path}')

    # If not, create a new vendor package and move the contents there
    else:
        sort_path = new_vendor_package.main([vendor], incoming=True)[0]
        download_path = sort_path
        print(f'Moving package contents to path: {sort_path}')
        for item in os.listdir(package):
            item_path = os.path.join(package, item)
            _move_package(item_path, sort_path)

    # Remove the empty container folder 'PKG - {package_name}' from default download location
    if len(os.listdir(package)) == 0:
        print(f'Cleaning up empty package folder: {package}')
        os.rmdir(package)

    print(f'Downloaded package {package_name} to path: {download_path}.')


def _get_sub_package_path(package):
    package_name_strip = _get_package_name_strip(package)
    sub_package_path = None
    if _is_valid_package_name(package_name_strip):
        sub_package_path = os.path.join(package, package_name_strip)
    return sub_package_path


def _get_package_name_strip(package):
    package_name = os.path.basename(package)
    return package_name.replace('PKG - ', '')


def _is_valid_package_name(package_name):
    pattern = re.compile(PACKAGE_REGEX)
    match = re.match(pattern, package_name)
    if match:
        return True
    return False


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
