from python.distant_vfx.jobs import exiftool_rename_cr2_dir
import sys


# A quick entry point for the exiftool_rename_dir job.
def main():
    exiftool_rename_cr2_dir.main(sys.argv[1:])


if __name__ == '__main__':
    main()
