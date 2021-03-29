#!/bin/env python3

import argparse
import yaml

from python.distant_vfx.jobs import aspera_send
from python.distant_vfx.jobs import fmp_manual_inject
from python.distant_vfx.constants import ASPERA_YML_PATH


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

    parser.add_argument(
        '--inject',
        action='store_true',
        help='Optionally specify whether to inject the delivery into FileMaker.'
    )

    args = parser.parse_args()

    with open(ASPERA_YML_PATH, 'r') as file:
        faspex_data = yaml.safe_load(file)

    for vendor in args.vendors:
        host = _get_host(vendor, faspex_data)
        if not host:
            raise ValueError(f'Could not find vendor in Aspera faspex host data.')
        else:
            aspera_send.main(
                user=faspex_data[host]['user'],
                password=faspex_data[host]['password'],
                url=faspex_data[host]['base_url'],
                package_id_json_file=faspex_data[host]['json_file'],
                recipients=faspex_data[host]['vendors'][vendor]['recipients'],
                url_prefix=faspex_data[host]['prefix'],
                content_protect_password=faspex_data[host]['content_protect_password'],
                filepath=args.path,
                title=args.title,
                vendor=vendor,
                email=faspex_data[host]['vendors'][vendor]['email'],
                note=args.note,
                cc_on_upload=faspex_data[host]['vendors'][vendor]['cc_on_upload'],
                cc_on_download=faspex_data[host]['vendors'][vendor]['cc_on_download']
            )

    if args.inject:
        fmp_manual_inject.main(args.path)


def _get_host(vendor, faspex_data):
    for host, host_data in faspex_data.items():
        for vendor_, vendor_data in host_data['vendors'].items():
            if vendor in vendor_:
                return host
    return None


if __name__ == '__main__':
    main()
