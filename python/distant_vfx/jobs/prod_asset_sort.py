import os
import subprocess

ASSETS_BASE_PATH = '/mnt/Projects/dst/production/assets'
# ASSETS_BASE_PATH = '/Users/marklivolsi/Desktop/out/assets'  # For testing

SLATES_BASE_PATH = '/mnt/Projects/dst/production/assets/refSlates'  # TODO: may need to change this
# SLATES_BASE_PATH = '/Users/marklivolsi/Desktop/out/refSlates'  # For testing

MANUAL_SORT_BASE_PATH = '/mnt/Projects/dst/production/zManualSort'  # TODO: Add this
# MANUAL_SORT_BASE_PATH = '/Users/marklivolsi/Desktop/out/manualSort'  # For testing


ASSET_PREFIXES = ['char', 'dd', 'env', 'prop', 'prp', 'vhcl', 'ext']

TYPE_MAP = {
    'rsMPC': 'rs',
    'pbMPC': 'pb',
    'texMPC': 'tex',
    'text': 'tex',
    'textMPC': 'tex',
    'pgMPC': 'pg',
    'hdriMPC': 'hdri',
    'refMPC': 'ref',
    'witMPC': 'wit',
    'movMPC': 'mov',
    'slateMPC': 'slate'
}


# Get the type of the item based on the name (e.g. asset, slate). Assumes 'tree' is installed.
def get_type(item_type, item_name):

    if item_type is None or item_name is None:
        return None

    if item_type == 'slate':
        return 'slate'

    for prefix in ASSET_PREFIXES:
        if item_name.lower().startswith(prefix):
            return 'asset'

    num_alphas = sum(c.isalpha() for c in item_name)
    num_digits = sum(c.isdigit() for c in item_name)

    if num_alphas <= 4 and num_digits <= 4:
        return 'slate'

    else:
        return None


def main(pkg_path):

    # Generate a log file of the package contents prior to sorting
    log_file = os.path.basename(pkg_path) + '_log.txt'
    log_path = os.path.join(pkg_path, log_file)
    cmd = ['tree', pkg_path, '-o', log_path]
    print('Creating log file for path: {}'.format(pkg_path))
    result = subprocess.run(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            universal_newlines=True,
                            shell=False)

    # Iterate through the provided package
    for item in os.listdir(pkg_path):

        # Skip over the log file
        if item == log_file or item == '.DS_Store':
            continue

        # Get the full path of the item
        src_path = os.path.join(pkg_path, item)
        print('Found item: {}'.format(item))

        # Set a manual sort flag
        manual_sort = False

        # Get the item type and asset / slate name
        try:
            item_split = item.split('_')
            item_type = item_split[0]
            item_name = item_split[1]
        except IndexError:
            item_type = None
            item_name = None

        # Standardize the item type
        if item_type in TYPE_MAP:
            item_type_fmt = TYPE_MAP[item_type.lower()]
        else:
            item_type_fmt = item_type.lower()

        # TODO: Do we want to use exiftool to rename folders?

        # Get the destination path based on item type
        if get_type(item_type_fmt, item_name) == 'asset':
            dest_path = os.path.join(ASSETS_BASE_PATH, item_name, item_type_fmt)
        elif get_type(item_type_fmt, item_name) == 'slate':
            dest_path = os.path.join(SLATES_BASE_PATH, item_name, item_type_fmt)
        else:

            # If the item is not sortable, it will go to the manual sort directory
            dest_path = MANUAL_SORT_BASE_PATH
            manual_sort = True

        # Create destination path if it does not exist yet.
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)

        # If the item is sortable but already exists at the destination, move to manual sort path instead
        dest_item = os.path.join(dest_path, item)
        dest_item_exists = os.path.exists(dest_item)
        if dest_item_exists and not manual_sort:
            dest_path = MANUAL_SORT_BASE_PATH
            print('Item {} already exists at sort destination. Moving to manual sort path.'.format(item))

        # If the item is not sortable and already exists at the manual sort path, flag it but don't move it.
        elif dest_item_exists and manual_sort:
            print('Cannot sort item {} (already exists at manual sort path) {}'.format(item_name,
                                                                                       MANUAL_SORT_BASE_PATH))

        # Execute the move
        cmd = ['mv', src_path, dest_path]
        print('Moving item {} to destination: {}'.format(item, dest_path))
        result = subprocess.run(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                universal_newlines=True,
                                shell=False)

        # Print any output / errors to terminal
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
