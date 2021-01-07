import os
from collections import defaultdict
from functools import wraps

from .sequences import ImageSequence
from .constants import LEGAL_FRAME_EXTENSIONS


def dict_items_to_str(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        dictionary = func(*args, **kwargs)
        result = {str(key): ('' if value is None else str(value)) for key, value in dictionary.items()}
        return result
    return wrapper


def make_basename_map_from_file_path_list(file_path_list):
    basename_map = defaultdict(lambda: defaultdict(list))
    for path in file_path_list:
        filename = os.path.basename(path)
        split = filename.split('.')
        basename, extension = split[0], split[-1]
        basename_map[basename][extension].append(path)
    return basename_map


def parse_files_from_basename_map(basename_map):
    paths = []
    for basename, ext_map in basename_map.items():
        for ext, file_list in ext_map.items():
            num_files = len(file_list)
            ext_with_dot = ext + '.'
            if num_files > 1 and ext_with_dot in LEGAL_FRAME_EXTENSIONS:
                frame_filenames = [os.path.basename(path) for path in file_list]
                parent_dir = os.path.dirname(file_list[0])
                seq = ImageSequence(frame_filenames, parent_dir)
                # path = os.path.join(parent_dir, seq.name)  # TODO: DELETE ME
                # paths.append(seq.path)
                paths.append(seq)
            else:
                paths += file_list
    return paths
