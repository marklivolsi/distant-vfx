#!/usr/bin/env python3

from python.distant_vfx.screening import SupervisorScreening


# An entry point for the launch_ldq_review job
def main():
    screening = SupervisorScreening()
    screening.run()


if __name__ == '__main__':
    main()
