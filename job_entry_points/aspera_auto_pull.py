#!/bin/env python3

import argparse
import time

from python.distant_vfx.jobs import aspera_auto_download
from python.distant_vfx.constants import ASPERA_VENDOR_MAP, DEFAULT_DOWNLOAD_PATH


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--catch-up',
        action='store_true',
        help='Optionally specify "catch-up" mode, which updates the latest package ID without downloading '
             'any packages.'
    )

    args = parser.parse_args()

    DOWNLOAD_VENDORS = ['mrx', 'edt']

    while True:
        for vendor in DOWNLOAD_VENDORS:
            aspera_auto_download.main(
                user=ASPERA_VENDOR_MAP[vendor].get('user'),
                password=ASPERA_VENDOR_MAP[vendor].get('password'),
                url=ASPERA_VENDOR_MAP[vendor].get('url'),
                package_id_json_file=ASPERA_VENDOR_MAP[vendor].get('package_id_json_file'),
                url_prefix=ASPERA_VENDOR_MAP[vendor].get('url_prefix'),
                content_protect_password=ASPERA_VENDOR_MAP[vendor].get('content_protect_password'),
                output_path=DEFAULT_DOWNLOAD_PATH,
                vendor=vendor,
                catch_up_mode=args.catch_up
            )
        print('Package scan complete. Job will restart in 5 min.')
        if args.catch_up:
            break
        else:
            time.sleep(300)


if __name__ == '__main__':
    main()
