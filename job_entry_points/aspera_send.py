import argparse
from python.distant_vfx.jobs import aspera_send
from python.distant_vfx.constants import INTERNAL_FASPEX_BASE_URL, INTERNAL_FASPEX_USERNAME, INTERNAL_FASPEX_PASSWORD, \
    FASPEX_BASE_URL, FASPEX_USERNAME, FASPEX_PASSWORD, LAST_PROCESSED_PACKAGE_JSON_FILE_EXTERNAL_ASPERA, \
    LAST_PROCESSED_PACKAGE_JSON_FILE_INTERNAL_ASPERA, INTERNAL_FASPEX_CONTENT_PROTECT_PASSWORD, FASPEX_RECIPIENTS, \
    INTERNAL_FASPEX_RECIPIENTS


VENDOR_MAP = {
    'mrx': {
        'user': FASPEX_USERNAME,
        'password': FASPEX_PASSWORD,
        'url': FASPEX_BASE_URL,
        'package_id_json_file': LAST_PROCESSED_PACKAGE_JSON_FILE_EXTERNAL_ASPERA,
        'recipients': FASPEX_RECIPIENTS.split(','),
    },
    'edt': {
        'user': INTERNAL_FASPEX_USERNAME,
        'password': INTERNAL_FASPEX_PASSWORD,
        'url': INTERNAL_FASPEX_BASE_URL,
        'package_id_json_file': LAST_PROCESSED_PACKAGE_JSON_FILE_INTERNAL_ASPERA,
        'url_prefix': 'faspex',
        'recipients': INTERNAL_FASPEX_RECIPIENTS.split(','),
        'content_protect_password': INTERNAL_FASPEX_CONTENT_PROTECT_PASSWORD
    }
}


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

    args = parser.parse_args()

    for vendor in args.vendors:
        legal_vendors = VENDOR_MAP.keys()
        if vendor not in legal_vendors:
            raise ValueError(f'Vendors must be from this list {legal_vendors}')
        else:
            aspera_send.main(
                user=VENDOR_MAP[vendor].get('user'),
                password=VENDOR_MAP[vendor].get('password'),
                url=VENDOR_MAP[vendor].get('url'),
                package_id_json_file=VENDOR_MAP[vendor].get('package_id_json_file'),
                recipients=VENDOR_MAP[vendor].get('recipients'),
                url_prefix=VENDOR_MAP[vendor].get('url_prefix'),
                content_protect_password=VENDOR_MAP[vendor].get('content_protect_password'),
                filepath=args.path,
                title=args.title
                # TODO : Add CC on upload / download
            )
