#!/usr/bin/env python3

import argparse
from distant_vfx.jobs import fmp_manual_inject


# A quick entry point for the fmp_manual_inject job
def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--input',
                        action='store',
                        type=str,
                        required=True,
                        nargs='+',
                        help='<required> Specify one or more packages to inject into FileMaker.')

    args = parser.parse_args()

    for path in args.input:
        fmp_manual_inject.main(path)


if __name__ == '__main__':
    main()
