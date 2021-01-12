#!/usr/bin/env python3

import argparse
from python.distant_vfx.jobs import inject_scan_order_edl


# An entry point for the inject_scan_order_edl job
def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'input',
        action='store',
        nargs='+',
        type=str,
        help='<required> Specify one or more scan order edl file paths.'
    )

    parser.add_argument(
        '--csv',
        action='store_true',
        help='Specifying --csv will output scan order data to csv files instead of injecting to FileMaker.'
    )

    parser.add_argument(
        '--stills',
        action='store_true',
        help='Specifying --stills will additionally inject stills located within the same directory as the EDL '
             'to FileMaker. Please note that this will recursively search the EDL directory for stills, so please do '
             'not use this option if the EDL is not contained within its own directory.'
    )

    args = parser.parse_args()

    for edl_path in args.input:
        inject_scan_order_edl.main(edl_path, csv_out=args.csv, inject_stills=args.stills)


if __name__ == '__main__':
    main()
