import argparse
from python.distant_vfx.jobs import prod_asset_sort


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input',
                        action='store',
                        nargs='+',
                        required=True,
                        help='<required> Specify one or more directory paths whose contents should be sorted.')

    args = parser.parse_args()

    for arg in args.input:
        prod_asset_sort.main(arg)


if __name__ == '__main__':
    main()
