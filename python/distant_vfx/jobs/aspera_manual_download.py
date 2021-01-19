import os
import re
import subprocess
import traceback
import sys
import yagmail
from ..aspera import AsperaCLI
from ..constants import PACKAGE_REGEX, MAILBOX_BASE_PATH, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_RECIPIENTS


def main(user, password, url, package_id_json_file, url_prefix, output_path, content_protect_password, package_name):

    aspera = AsperaCLI(
        user=user,
        password=password,
        url=url,
        package_id_json_file=package_id_json_file,
        url_prefix=url_prefix
    )

    package = None
    try:
        package = aspera.download_package_by_name(
            package_name=package_name,
            output_path=output_path,
            content_protect_password=content_protect_password
        )
    except:
        traceback.print_exc()

    if not package:
        print(f'No package found with title {package_name}')
        return

    package_root_contents = os.listdir(package)
    package_root_contents = [p for p in package_root_contents if not p.startswith('.')]
    package_name = os.path.basename(package)

    sub_package_name = package_root_contents[0]
    sub_package_path = os.path.join(package, sub_package_name)

    if (len(package_root_contents) != 1) or \
            (sub_package_name not in package_name) or \
            (not _is_valid_package_name(sub_package_name)) or \
            (not os.path.isdir(sub_package_path)):
        # Then contents are not a sub package and can't be sorted. Leave it in default download location.
        print(f'Package {package_name} cannot be sorted, leaving in default download location.')

    else:
        # Otherwise, we have a package inside a 'PKG - {package name}' container
        split = sub_package_path.split('_')
        from_vendor = split[1]
        sort_path = os.path.join(MAILBOX_BASE_PATH, from_vendor, f'fr_{from_vendor}')

        # Move package to mailbox
        _move_package(sub_package_path, sort_path)

        # Remove empty 'PKG' dir, ONLY if empty
        _remove_empty_container_dir(package)

        print(f'Downloaded package {package_name} to path: {sort_path}.')

    # # Send an email notification
    # subject = f'[DISTANT_API] Downloaded package {package_name}'
    # yag = yagmail.SMTP(
    #     user=EMAIL_USERNAME,
    #     password=EMAIL_PASSWORD
    # )
    # yag.send(
    #     to=EMAIL_RECIPIENTS.split(','),
    #     subject=subject,
    #     contents=message
    # )


def _is_valid_package_name(package_name):
    pattern = re.compile(PACKAGE_REGEX)
    match = re.match(pattern, package_name)
    if match:
        return True
    return False


def _remove_empty_container_dir(path):
    if len(os.listdir(path)) == 0:
        os.rmdir(path)


def _move_package(source, dest):
    cmd = ['mv', source, dest]
    dest_folder = os.path.basename(source)
    dest_path = os.path.join(dest, dest_folder)
    if os.path.exists(dest_path):
        print(f'File already exists: {dest_path}')
        sys.exit()
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
        pass
        # send email



