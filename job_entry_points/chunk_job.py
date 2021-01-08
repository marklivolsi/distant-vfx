#!/usr/bin/env python3

import argparse
from python.distant_vfx.jobs import chunk_to_new_packages


# A quick entry point for the chunk_to_new_packages job.
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output',
                        action='store',
                        type=str,
                        required=True,
                        help='<required> Specify an output directory.')
    parser.add_argument('-m', '--move',
                        action='store_true',
                        help='Set chunk operation to move (rather than copy).')
    parser.add_argument('-i', '--input',
                        action='store',
                        nargs='+',
                        required=True,
                        help='<required> Specify one or more directory paths whose contents should be chunked.')

    args = parser.parse_args()
    chunk_to_new_packages.main(args.output,
                               args.input,
                               should_move=args.move)


if __name__ == '__main__':
    main()
