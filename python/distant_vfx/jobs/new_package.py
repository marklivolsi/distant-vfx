from datetime import datetime
import itertools
import os
import string
import sys


def main(root_path):

    vendor = root_path.split('_')[1]
    show = 'dst'
    date = datetime.now().strftime('%Y%m%d')
    base_pkg_name = vendor + '_' + show + '_' + date + '_'
    packages_from_today = [pkg for pkg in os.listdir(root_path) if base_pkg_name in pkg]

    # Necessary to make sure we iterate up to 'aa' after 'z'
    max_len = len(packages_from_today[0])
    for pkg in packages_from_today:
        pkg_len = len(pkg)
        if pkg_len > max_len:
            max_len = pkg_len

    packages_from_today = [pkg for pkg in packages_from_today if len(pkg) == max_len]

    if not packages_from_today:
        full_pkg_name = base_pkg_name + 'a'
    else:
        latest_pkg = max(packages_from_today)
        print(latest_pkg)
        latest_alpha = latest_pkg.split('_')[-1]
        print(latest_alpha)
        alpha = (''.join(letters) for length in range(1, 3) for letters in itertools.product(string.ascii_lowercase, repeat=length))
        while True:
            next_alpha = next(alpha)
            if latest_alpha in next_alpha:
                break
        next_alpha = next(alpha)
        full_pkg_name = base_pkg_name + next_alpha

    path = os.path.join(root_path, full_pkg_name)
    os.mkdir(path)


if __name__ == '__main__':
    main(sys.argv[1])
