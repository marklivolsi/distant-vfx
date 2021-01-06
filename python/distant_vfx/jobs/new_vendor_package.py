import os
from . import new_package
from ..constants import MAILBOX_BASE_PATH


def main(vendor_codes, num_packages=1):
    for vendor_code in vendor_codes:
        to_vendor_folder = f'to_{vendor_code}'
        to_vendor_path = os.path.join(MAILBOX_BASE_PATH, vendor_code, to_vendor_folder)
        for _ in range(num_packages):
            new_package.main(root_path=to_vendor_path)
