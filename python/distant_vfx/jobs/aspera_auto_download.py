import os
import re
import subprocess
from ..aspera import AsperaCLI
from ..constants import PACKAGE_REGEX, MAILBOX_BASE_PATH


def main(user, password, url, package_id_json_file, url_prefix, output_path, content_protect_password):

    aspera = AsperaCLI(
        user=user,
        password=password,
        url=url,
        package_id_json_file=package_id_json_file,
        url_prefix=url_prefix
    )

    downloaded_packages = aspera.download_new_packages(
        output_path=output_path,
        content_protect_password=content_protect_password
    )

    if not downloaded_packages:
        return

    for package in downloaded_packages:
        package_root_contents = os.listdir(package)
        package_root_contents = [p for p in package_root_contents if not p.startswith('.')]
        package_name = os.path.basename(package)

        if not len(package_root_contents) == 1:
            # Then contents are not a sub package and can't be sorted. Leave it in default download location.
            continue

        sub_package_name = package_root_contents[0]
        sub_package_path = os.path.join(package, sub_package_name)

        if sub_package_name not in package_name:
            continue

        elif not _is_valid_package_name(sub_package_name):
            continue

        elif not os.path.isdir(sub_package_path):
            continue

        # Otherwise, we have a package inside a 'PKG - {package name}' container
        split = sub_package_path.split('_')
        from_vendor = split[1]
        sort_path = os.path.join(MAILBOX_BASE_PATH, from_vendor, f'fr_{from_vendor}')

        # Move package to mailbox
        _move_package(sub_package_path, sort_path)

        # Remove empty 'PKG' dir, ONLY if empty
        _remove_empty_container_dir(package)


def _remove_empty_container_dir(path):
    if len(os.listdir(path)) == 0:
        os.rmdir(path)


def _move_package(source, dest):
    cmd = ['mv', source, dest]
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


def _is_valid_package_name(package_name):
    pattern = re.compile(PACKAGE_REGEX)
    match = re.match(pattern, package_name)
    if match:
        return True
    return False