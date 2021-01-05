#!/usr/bin/env python3

import argparse
from distant_vfx.jobs import inject_excel_notes


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('xlsx_paths',
                        type=str,
                        nargs='+',
                        help='Specify one or more file paths for .xlsx note documents to import to FileMaker.')

    args = parser.parse_args()

    for path in args.xlsx_paths:
        inject_excel_notes.main(xlsx_path=path)


if __name__ == '__main__':
    main()
