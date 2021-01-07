import os
import subprocess
import sys
from .filemaker import CloudServerWrapper
from .constants import RV_PATH, FMP_URL, FMP_USERNAME, FMP_PASSWORD, FMP_VFX_DB, FMP_VERSIONS_LAYOUT, FMP_NOTES_LAYOUT, \
    SHOT_TREE_BASE_PATH


class Screening:

    def __init__(self, screening_id):
        self.screening_id = int(screening_id)
        self.query = self._set_query()
        self.cut_order_map = {}
        self.file_paths = []

    def _get_query_layout(self):
        return FMP_NOTES_LAYOUT

    def _set_query(self):
        return {'ScreeningID': self.screening_id}

    def run(self):
        print('Searching for review files, please wait...')
        records = self._get_records_from_filemaker()

        if not records:
            print('No review records found.')
            sys.exit()

        for version_record in records:
            version_name = self._get_version_name_from_record(version_record)
            path = self._get_filepath_from_record(version_record)

            if path is None:
                if version_name is not None:
                    path = self._find_missing_filepath(version_name)  # defaults to dnx mov files
                    if path is None:
                        print(f'Could not locate version on disk: {version_name}')
                        continue
                else:
                    print(f'Cannot locate version name or path for record, skipping. (Record data: {version_record})')
                    continue

            # If we get here, we have a path to the version
            print(f'Found file: {path}')
            cut_order = self._get_cut_order_from_record(version_record)
            self.cut_order_map[path] = cut_order
            self.file_paths.append(path)

        # Sort files by cut order, then alphabetically
        self.file_paths = sorted(self.file_paths, key=lambda x: (self.cut_order_map[x], x))

        # Launch files in RV
        print('Launching files in RV...')
        self.launch_rv(self.file_paths)

    def _get_records_from_filemaker(self):
        with CloudServerWrapper(url=FMP_URL,
                                user=FMP_USERNAME,
                                password=FMP_PASSWORD,
                                database=FMP_VFX_DB,
                                layout=self._get_query_layout()
                                ) as fmp:
            fmp.login()

            records = None
            try:
                records = fmp.find([self.query], limit=500)
            except:
                if fmp.last_error == 401:
                    pass
                else:
                    raise
            return records

    @staticmethod
    def _get_cut_order_from_record(record):
        try:
            cut_order = int(record['VFXEditorialShots::CutOrder'])
        except:
            cut_order = 999999999  # put shots without cut order at the back of the list
        return cut_order

    @staticmethod
    def _get_shot_dir_path(filename):
        vfx_id = filename[:7]
        seq = vfx_id[:3]
        shot_dir_path = os.path.join(SHOT_TREE_BASE_PATH, seq, vfx_id)
        return shot_dir_path

    @staticmethod
    def _get_ref_dir_path(filename):
        seq = filename[:3]
        ref_path = os.path.join(SHOT_TREE_BASE_PATH, seq, '_reference')
        return ref_path

    @staticmethod
    def _get_version_name_from_record(record):
        try:
            version_name = record.Filename
            return version_name
        except:
            return None

    @staticmethod
    def _get_filepath_from_record(record):
        try:
            path = record.Path
            if not path:
                return None
            return path
        except AttributeError:
            return None

    def _find_missing_filepath(self, version_name, identifier='dnx'):
        paths = self._find_all_matching_filepaths(version_name, self._get_shot_dir_path(version_name))

        # If no paths found in shot dir, try ref dir
        if not paths:
            ref_path = self._get_ref_dir_path(version_name)
            paths = self._find_all_matching_filepaths(version_name, ref_path)

        if paths:
            for path in paths:
                if identifier.lower() in path.lower():
                    return path
            return paths[0]  # if nothing matches identifier, default to the first file found
        return None

    def _find_all_matching_filepaths(self, version_name, root_path):
        paths = []
        for root, dirs, files in os.walk(root_path):
            for file in files:
                path = os.path.join(root, file)
                if self._is_frame_range(path):  # currently will skip over frame ranges
                    break
                else:
                    if version_name.lower() in file.lower():
                        paths.append(path)
        return paths

    @staticmethod
    def _is_frame_range(filepath):
        return os.path.splitext(filepath)[1] in ['.exr']

    @staticmethod
    def launch_rv(paths):
        cmd = [RV_PATH]
        for path in paths:
            cmd.append(path)

        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True,
                                   shell=False)
        stdout, stderr = process.communicate()


class SupervisorScreening(Screening):

    def __init__(self):
        super().__init__(screening_id=0)

    def _get_query_layout(self):
        return FMP_VERSIONS_LAYOUT

    def _set_query(self):
        return {'SupReviewFlag': 1}
