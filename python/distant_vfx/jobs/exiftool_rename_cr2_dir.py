from dateutil.parser import parse
import subprocess
import os
import json


# Rename the parent directory containing cr2 files based on the CreateDate of the first cr2 in the directory.
def main(paths):

    # Walk through the provided paths recursively to find cr2 files.
    for path in paths:
        for root, dirs, files in os.walk(path):

            # Filter the files to only include .cr2
            cr2s = list(filter(lambda x: os.path.splitext(x)[1] == '.cr2', files))

            if cr2s:

                # Grab the path to the first cr2 file
                cr2s.sort()
                first_cr2 = cr2s[0]
                cr2_path = os.path.join(root, first_cr2)

                # Use exiftool to get the image metadata
                cmd = ['exiftool', '-json', cr2_path]
                process = subprocess.Popen(cmd,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        universal_newlines=True,
                                        shell=False)
                stdout, _ = process.communicate()
                exif_data = stdout
                exif_json = json.loads(exif_data)[0]

                # Extract the created datetime and format it
                date_time_fmt = None
                if 'CreateDate' in exif_json:
                    create_date = exif_json['CreateDate']
                    date_time_split = create_date.split()
                    date, time = date_time_split[0].replace(':', '/'), date_time_split[1]
                    date_fmt = parse(date).strftime('%Y%m%d')
                    time_fmt = parse(time).strftime('%H%M%S')
                    date_time_fmt = date_fmt + '_' + time_fmt

                # Rename the cr2 parent dir, appending the created datetime
                if date_time_fmt is not None:
                    parent_dir = os.path.dirname(cr2_path)
                    new_parent_dir_path = parent_dir.parent / (parent_dir.name + '_' + date_time_fmt)
                    os.rename(parent_dir, new_parent_dir_path)
