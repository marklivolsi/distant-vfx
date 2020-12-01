import os
import subprocess

ASSETS_BASE_PATH = '/mnt/Projects/dst/production/assets'
SLATES_BASE_PATH = '/mnt/Projects/dst/production/refslates'  # TODO: may need to change this
MANUAL_SORT_BASE_PATH = ''  # TODO: Add this

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
    'movMPC': 'mov'
}


# Get the type of the item based on the name (e.g. asset, slate)
def get_type(item_name):
    for prefix in ASSET_PREFIXES:
        if item_name.lower().startswith(prefix):
            return 'asset'
    return 'slate'


def main(pkg_path):

    # Iterate through the provided package
    for item in os.listdir(pkg_path):

        # Get the full path of the package
        src_path = os.path.join(pkg_path, item)
        print('Scanning path: {}\n'.format(src_path))

        # Get the item type and asset / slate name
        item_split = item.split('_')
        item_type = item_split[0]
        item_name = item_split[1]

        # Standardize the item type
        if item_type in TYPE_MAP:
            item_type_fmt = TYPE_MAP[item_type]
        else:
            item_type_fmt = item_type

        # Set a manual sort flag
        manual_sort = False

        # TODO: Do we want to use exiftool to rename folders at this point?

        # Get the destination path based on item type
        if get_type(item_name) == 'asset':
            dest_path = os.path.join(ASSETS_BASE_PATH, item_name, item_type_fmt)
        elif get_type(item_name) == 'slate':
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

        # If the item is not sortable and already exists at the manual sort path, flag it but don't move it.
        elif dest_item_exists and manual_sort:
            print('Cannot sort item {} (already exists at manual sort path) {}\n'.format(item_name,
                                                                                         MANUAL_SORT_BASE_PATH))

        # Execute the move
        cmd = ['mv', src_path, dest_path]
        print('Moving item {} to destination: {}\n'.format(item_name, dest_path))
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
