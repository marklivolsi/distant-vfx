#!/usr/bin/env python3

import argparse
from distant_vfx.jobs import launch_screening


# An entry point for the launch_screening job
def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('screening_id',
                        type=int,
                        required=True,
                        help='<required> The ID of the screening to launch in RV.')

    args = parser.parse_args()

    launch_screening.main(screening_id=args.screening_id)


if __name__ == '__main__':
    main()
