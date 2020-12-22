import os
from collections import defaultdict


def make_basename_map_from_file_path_list(file_path_list):
    basename_map = defaultdict(lambda: defaultdict(list))
    for path in file_path_list:
        filename = os.path.basename(path)
        split = filename.split('.')
        basename, extension = split[0], split[-1]
        basename_map[basename][extension].append(path)
    return basename_map
