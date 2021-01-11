import argparse
from python.distant_vfx.screening import FastFindMovie


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('vfxid',
                        action='store',
                        type=str,
                        help='The VFX ID of the shot you want to find.')

    parser.add_argument('--num',
                        action='store',
                        type=int,
                        help='The number of versions to retrieve (starting with the most recent and working backward.')

    args = parser.parse_args()
    if args.num_versions:
        ffm = FastFindMovie(vfxid=args.vfxid,
                            num_versions=args.num)
    else:
        ffm = FastFindMovie(vfxid=args.vfxid)

    ffm.run()


if __name__ == '__main__':
    main()
