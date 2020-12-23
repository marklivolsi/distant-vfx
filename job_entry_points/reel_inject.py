#!/usr/bin/env python3

import argparse
from distant_vfx.jobs import inject_reel_edl


# An entry point for the inject_reel_edl job
def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-i', '--input',
        action='store',
        nargs='+',
        type=str,
        required=True,
        help='<required> Specify one or more reel edl file paths.'
    )

    parser.add_argument(
        '--csv',
        action='store_true',
        help='Specifying --csv will output reel data to csv files instead of injecting to FileMaker.'
    )

    args = parser.parse_args()

    for edl_path in args.input:
        inject_reel_edl.main(edl_path, csv_out=args.csv)


if __name__ == '__main__':
    main()
