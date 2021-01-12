#!/usr/bin/env python3

from python.distant_vfx.screening import DirectorScreening


# An entry point for the launch_ldq_review job
def main():
    screening = DirectorScreening()
    screening.run()


if __name__ == '__main__':
    main()
