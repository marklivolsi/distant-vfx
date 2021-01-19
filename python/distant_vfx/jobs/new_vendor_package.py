import os
from . import new_package
from ..constants import MAILBOX_BASE_PATH


def main(vendor_codes, num_packages=1, incoming=False):
    paths = []
    for vendor_code in vendor_codes:
        if incoming:
            vendor_folder = f'fr_{vendor_code}'
        else:
            vendor_folder = f'to_{vendor_code}'
        vendor_path = os.path.join(MAILBOX_BASE_PATH, vendor_code, vendor_folder)
        for _ in range(num_packages):
            path = new_package.main(root_path=vendor_path, incoming=incoming)
            paths.append(path)
    return paths
