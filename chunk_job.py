from python.distant_vfx.jobs import chunk_to_new_packages
import argparse


# A quick entry point for the chunk_to_new_packages job.
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', action='store', type=str, required=True)
    parser.add_argument('-m', '--move', action='store_true')
    parser.add_argument('-i', '--input', action='store', nargs='+', required=True)

    args = parser.parse_args()
    chunk_to_new_packages.main(args.output,
                               args.input,
                               should_move=args.move)


if __name__ == '__main__':
    main()
