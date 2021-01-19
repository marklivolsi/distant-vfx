import itertools
import os
import string
from datetime import datetime

from ..constants import SHOW_CODE


# Create a new package by scanning a directory for existing packages and iterating up as appropriate
def main(root_path, incoming=False):

    # Format the base package name
    vendor = root_path.rsplit('_', 1)[1]
    show = SHOW_CODE
    date = datetime.now().strftime('%Y%m%d')
    if incoming:
        base_pkg_name = show + '_' + vendor + '_' + date + '_'
    else:
        base_pkg_name = vendor + '_' + show + '_' + date + '_'

    # Check the root path for packages matching the base name (packages from today)
    packages_from_today = [pkg for pkg in os.listdir(root_path) if base_pkg_name in pkg]

    # If no packages from today, start with letter 'a'
    if not packages_from_today:
        full_pkg_name = base_pkg_name + 'a'

    # Otherwise, iterate up a->z, (aa->zz if necessary)
    else:
        # Necessary to make sure we iterate up to 'aa' after 'z'
        max_len = len(packages_from_today[0])
        for pkg in packages_from_today:
            pkg_len = len(pkg)
            if pkg_len > max_len:
                max_len = pkg_len
        packages_from_today = [pkg for pkg in packages_from_today if len(pkg) == max_len]

        latest_pkg = max(packages_from_today)
        latest_alpha = latest_pkg.split('_')[-1]

        # Generator to iterate a -> zz, generates each value on demand with next()
        alpha = (''.join(letters)
                 for length in range(1, 3)
                 for letters in itertools.product(string.ascii_lowercase, repeat=length))
        while True:
            next_alpha = next(alpha)
            if latest_alpha in next_alpha:
                break
        next_alpha = next(alpha)
        full_pkg_name = base_pkg_name + next_alpha

    # Create the new package directory
    path = os.path.join(root_path, full_pkg_name)
    print('Creating new package directory: {}'.format(path))
    os.mkdir(path)

    return path
