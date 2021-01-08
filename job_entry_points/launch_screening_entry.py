#!/usr/bin/env python3

import argparse
from python.distant_vfx.screening import Screening


# An entry point for the launch_screening job
def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('screening_id',
                        type=int,
                        help='<required> The ID of the screening to launch in RV.')

    args = parser.parse_args()

    screening = Screening(args.screening_id)
    screening.run()


if __name__ == '__main__':
    main()
