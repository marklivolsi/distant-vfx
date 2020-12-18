from collections import defaultdict
import os


IMG_SEQ_EXTS = ['exr']


def _parse_img_seq_paths(basename_map):
    img_seq_paths = []
    for basename, file_list in basename_map.items():
        for (ext, path) in file_list:
            if ext in IMG_SEQ_EXTS:
                parent_dir = os.path.dirname(path)
                img_seq_paths.append(parent_dir)
    return img_seq_paths


def _make_basename_map(filepath_list, include_ext):
    basename_map = defaultdict(list)
    for path in filepath_list:
        filename = os.path.basename(path)
        split = filename.split('.')
        basename, ext = split[0], split[-1]
        if ext in include_ext:
            if basename_map[basename]:
                for item in basename_map[basename]:
                    if ext in item[0]:
                        break  # only grab one frame of a framerange for each basename
                    else:
                        basename_map[basename].append((ext, path))
            else:
                basename_map[basename].append((ext, path))
    return basename_map


def _scan_files(root_path):
    for root, dirs, files in os.walk(root_path):
        for file in files:
            path = os.path.join(root, file)
            yield path
