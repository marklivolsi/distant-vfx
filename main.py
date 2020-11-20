from python.distant_vfx.jobs import chunk_to_new_packages
import sys


def main():
    chunk_to_new_packages.main(sys.argv[1], sys.argv[2:])


if __name__ == '__main__':
    main()
