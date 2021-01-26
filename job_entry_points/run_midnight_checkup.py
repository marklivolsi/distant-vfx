#!/bin/env python3

import sys
sys.path.append('/mnt/Plugins/python3.6')
sys.path.append('/mnt/Plugins/python3.6/lib')

import datetime as dt
import time
from python.distant_vfx.filemaker import CloudServerWrapper
from python.distant_vfx.constants import FMP_URL, FMP_USERNAME, FMP_PASSWORD, FMP_SPLASH_DB, FMP_SPLASH_LAYOUT, \
    FMP_MIDNIGHT_CHECKUP_SCRIPT


def main():

    while True:
        wait_for_target_hour(3)  # run at 3am
        with CloudServerWrapper(url=FMP_URL,
                                user=FMP_USERNAME,
                                password=FMP_PASSWORD,
                                database=FMP_SPLASH_DB,
                                layout=FMP_SPLASH_LAYOUT
                                ) as fmp:
            fmp.login()
            script_res = fmp.perform_script(name=FMP_MIDNIGHT_CHECKUP_SCRIPT)


def wait_for_target_hour(target_hour):
    now = dt.datetime.now()
    target = dt.datetime.combine(dt.date.today(), dt.time(hour=target_hour))
    if target < now:
        target += dt.timedelta(days=1)  # run once daily
    time.sleep((target - now).total_seconds())


if __name__ == '__main__':
    main()
