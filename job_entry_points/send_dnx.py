#!/bin/env python3

import argparse
from distant_vfx.jobs import send_dnx


# A quick entry point for the send_dnx job.
def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('input',
                        action='store',
                        type=str,
                        nargs='+',
                        help='<required> Specify one or more root paths from which to find and copy dnx files.')

    parser.add_argument('-o', '--output',
                        action='store',
                        type=str,
                        help='Specify an optional output directory. If none is provided, will default to edt mailbox')

    parser.add_argument('-n', '--no_delivery',
                        action='store_false',
                        help='Specifies that a new delivery package folder should not be made. If this option is '
                             'selected, files will be copied directly to the provided output directory. Defaults to '
                             'False (new delivery packages will be created by default).')

    args = parser.parse_args()

    for item in args.input:
        if args.output:
            send_dnx.main(scan_dir=item,
                          output_dir=args.output,
                          new_delivery=args.no_delivery)
        else:
            send_dnx.main(scan_dir=item,
                          new_delivery=args.no_delivery)


if __name__ == '__main__':
    main()
