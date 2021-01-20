#!/bin/env python3

import argparse
from python.distant_vfx.jobs import aspera_send
from python.distant_vfx.constants import ASPERA_VENDOR_MAP


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'path',
        action='store',
        type=str,
        help='Specify a package path to send.'
    )

    parser.add_argument(
        'title',
        action='store',
        type=str,
        help='Title for the package you want to send'
    )

    parser.add_argument(
        'vendors',
        nargs='+',
        action='store',
        type=str,
        help='Specify one or more vendors to send a package to.'
    )

    parser.add_argument(
        '--email',
        action='store_true',
        help='Optionally specify to automatically send a delivery email for this package.'
    )

    parser.add_argument(
        '--note',
        type=str,
        action='store',
        help='Optionally specify a note to accompany your delivery email.'
    )

    args = parser.parse_args()

    for vendor in args.vendors:
        legal_vendors = ASPERA_VENDOR_MAP.keys()
        if vendor not in legal_vendors:
            raise ValueError(f'Vendors must be from this list {legal_vendors}')
        else:
            aspera_send.main(
                user=ASPERA_VENDOR_MAP[vendor].get('user'),
                password=ASPERA_VENDOR_MAP[vendor].get('password'),
                url=ASPERA_VENDOR_MAP[vendor].get('url'),
                package_id_json_file=ASPERA_VENDOR_MAP[vendor].get('package_id_json_file'),
                recipients=ASPERA_VENDOR_MAP[vendor].get('recipients').split(','),
                url_prefix=ASPERA_VENDOR_MAP[vendor].get('url_prefix'),
                content_protect_password=ASPERA_VENDOR_MAP[vendor].get('content_protect_password'),
                filepath=args.path,
                title=args.title,
                vendor=vendor,
                email=ASPERA_VENDOR_MAP[vendor].get('email_recipients').split(','),
                note=args.note,
                cc_on_upload=ASPERA_VENDOR_MAP[vendor].get('cc_on_upload').split(','),
                cc_on_download=ASPERA_VENDOR_MAP[vendor].get('cc_on_download').split(',')
            )


if __name__ == '__main__':
    main()
