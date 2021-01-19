#!/bin/env python3

import argparse
from python.distant_vfx.jobs import aspera_manual_download
from python.distant_vfx.constants import ASPERA_VENDOR_MAP, DEFAULT_DOWNLOAD_PATH


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'title',
        action='store',
        type=str,
        help='Title for the package you want to download'
    )

    parser.add_argument(
        'vendor',
        action='store',
        type=str,
        help='Specify the vendor code of the sender'
    )

    args = parser.parse_args()

    legal_vendors = ASPERA_VENDOR_MAP.keys()
    vendor = args.vendor
    if vendor not in legal_vendors:
        raise ValueError(f'Vendors must be from this list {legal_vendors}')

    aspera_manual_download.main(
        user=ASPERA_VENDOR_MAP[vendor].get('user'),
        password=ASPERA_VENDOR_MAP[vendor].get('password'),
        url=ASPERA_VENDOR_MAP[vendor].get('url'),
        package_id_json_file=ASPERA_VENDOR_MAP[vendor].get('package_id_json_file'),
        url_prefix=ASPERA_VENDOR_MAP[vendor].get('url_prefix'),
        content_protect_password=ASPERA_VENDOR_MAP[vendor].get('content_protect_password'),
        package_name=args.title,
        output_path=DEFAULT_DOWNLOAD_PATH,
        vendor=vendor
    )


if __name__ == '__main__':
    main()
