import glob
import os


def _find_cube_path_from_scan_dir(version_folder_data):
    "/mnt/Projects/dst/post/shot/vpd/vpd0070/shot/vpd0070_comp_v003/2156x1500_exr/vpd0070_comp_v003.%04d.exr"
    "/mnt/Projects/dst/post/scan/ftc1000_bg_v001/_cdl/versioned/ftc1000_bg_v001/luts/ftc1000_bg_v001.cube"
    post_folder = "/mnt/Projects/dst/post"

    version_shot = version_folder_data.get("shot")
    glob_name_template = "{shot}_{descriptor}_v{version}".format(
        shot=version_shot,
        descriptor="*",
        version="*"
    )

    scan_folder = os.path.join(
        post_folder, "scan"
    )

    glob_path = os.path.join(
        scan_folder,
        glob_name_template
    )

    scans = {}
    for matched_path in glob.iglob(glob_path):
        data_struct = descriptor_from_filename(matched_path)
        descriptor = data_struct.get("descriptor")
        version = data_struct.get("version")
        if descriptor not in scans:
            scans[descriptor] = {}

        if version not in scans[descriptor]:
            scans[descriptor][version] = {}

        scans[descriptor][version] = data_struct

    if "bg" in scans:
        # Use the bg first
        cube_path = search_for_cube_by_descriptor(
            descriptor="bg",
            plates=scans,
            root_dir=scan_folder
        )
        if cube_path:
            return cube_path
    for descriptor in scans:
        cube_path = search_for_cube_by_descriptor(
            descriptor=descriptor,
            plates=scans,
            root_dir=scan_folder
        )
        if cube_path:
            return cube_path
    return None


def _get_proj_seq_shot_descriptor_version(path):
    basename = os.path.basename(path).replace(".", "_")
    splits = basename.split("_")
    version_splits = [
        split[1:]
        for split in splits
        if split.startswith("v") and split[1:].isdigit()
    ]

    return (
        "dst",
        basename[:3].lower(),
        basename[:7].lower(),
        splits[1].lower() if len(splits) > 1 else "",
        version_splits[0] if len(version_splits) else "001"
    )


def descriptor_from_filename(filename):
    project, sequence, shot, descriptor, version = _get_proj_seq_shot_descriptor_version(filename)

    try:
        number_version = int(version)
    except:
        number_version = 1
    data_struct = {
        "project": project,
        "sequence": sequence,
        "shot": shot,
        "descriptor": descriptor,
        "version": number_version,
        "filename": filename,
    }

    return data_struct


def search_for_cube_by_descriptor(descriptor, plates, root_dir):
    # Use the bg first
    background_versions = plates.get(descriptor, [])
    for version_num in sorted(background_versions.keys(), reverse=True):
        data_struct = background_versions[version_num]

        cube_path = os.path.join(
            root_dir,
            data_struct.get("filename"),
            "_cdl",
            "versioned",
            data_struct.get("filename"),
            "luts",
            data_struct.get("filename") + ".cube"
        )
        if os.path.exists(cube_path):
            # Perfect! Use it!
            return cube_path
        cube_path = os.path.join(
            root_dir,
            data_struct.get("filename"),
            "_cdl",
            data_struct.get("filename") + ".cube"
        )
        if os.path.exists(cube_path):
            # Perfect! Use it!
            return cube_path
    return None


def _path_get_shot_lut_from_path(path):
    "/mnt/Projects/dst/post/shot/efp/efp0630/script/nuke/efp0630_tmpComp_ignore_v001.ahughes.nk"
    "/mnt/Projects/dst/post/shot/vpd/vpd0070/plate/vpd0070_bg01_v001/2156x1500_exr/vpd0070_bg01_v001.%04d.exr"
    "/mnt/Projects/dst/post/shot/vpd/vpd0070/shot/vpd0070_comp_v003/2156x1500_exr/vpd0070_comp_v003.%04d.exr"

    "/mnt/Projects/dst/post/shot/ftc/ftc1000/plate/ftc1000_bg_v001/_cdl/versioned/ftc1000_bg_v001/luts/ftc1000_bg_v001.cube"
    dirname_two = os.path.dirname(os.path.dirname(path))
    dirname_three = os.path.dirname(dirname_two)
    version_folder_name = os.path.basename(os.path.dirname(os.path.dirname(path)))
    print(dirname_three)
    if os.path.basename(dirname_three) == "shot":
        # We're dealing with a rendered image!
        shot_dir = os.path.dirname(dirname_three)
        plates_dir = os.path.join(shot_dir, "plate")
        plates = {}
        for folder_name in os.listdir(plates_dir):
            data_struct = descriptor_from_filename(folder_name)
            descriptor = data_struct.get("descriptor")
            version = data_struct.get("version")
            if descriptor not in plates:
                plates[descriptor] = {}

            if version not in plates[descriptor]:
                plates[descriptor][version] = {}

            plates[descriptor][version] = data_struct

        if "bg" in plates:
            # Use the bg first
            cube_path = search_for_cube_by_descriptor(
                descriptor="bg",
                plates=plates,
                root_dir=plates_dir
            )
            if cube_path:
                return cube_path
        for descriptor in plates:
            cube_path = search_for_cube_by_descriptor(
                descriptor=descriptor,
                plates=plates,
                root_dir=plates_dir
            )
            if cube_path:
                return cube_path

        # Can't find it in the plate dir. I guess we check the scan one. Legacy bug.
        data_struct_from_version_folder = descriptor_from_filename(version_folder_name)
        cube_path = _find_cube_path_from_scan_dir(
            version_folder_data=data_struct_from_version_folder,
        )
        return cube_path
    elif os.path.basename(dirname_three) == "plate":
        plates = {}
        folder_name = os.path.basename(dirname_two)
        data_struct = descriptor_from_filename(folder_name)
        descriptor = data_struct.get("descriptor")
        version = data_struct.get("version")
        plates[descriptor] = {}
        plates[descriptor][version] = data_struct

        cube_path = search_for_cube_by_descriptor(
            descriptor=descriptor,
            plates=plates,
            root_dir=dirname_three,
        )
        return cube_path

    elif os.path.basename(dirname_two) == "script":
        # We're dealing with a scene file!
        shot_dir = os.path.dirname(dirname_two)
        plates_dir = os.path.join(shot_dir, "plate")
        plates = {}
        for folder_name in os.listdir(plates_dir):
            data_struct = descriptor_from_filename(folder_name)
            descriptor = data_struct.get("descriptor")
            version = data_struct.get("version")
            if descriptor not in plates:
                plates[descriptor] = {}

            if version not in plates[descriptor]:
                plates[descriptor][version] = {}

            plates[descriptor][version] = data_struct

        if "bg" in plates:
            # Use the bg first
            cube_path = search_for_cube_by_descriptor(
                descriptor="bg",
                plates=plates,
                root_dir=plates_dir
            )
            if cube_path:
                return cube_path
        for descriptor in plates:
            cube_path = search_for_cube_by_descriptor(
                descriptor=descriptor,
                plates=plates,
                root_dir=plates_dir
            )
            if cube_path:
                return cube_path

        # Can't find it in the plate dir. I guess we check the scan one. Legacy bug.
        data_struct_from_version_folder = descriptor_from_filename(version_folder_name)
        cube_path = _find_cube_path_from_scan_dir(
            version_folder_data=data_struct_from_version_folder,
        )
        return cube_path

    else:
        print("Error _path_get_show_lut_from_path, only supports renders!")
        return None


def _path_get_show_lut_from_path(path):
    # if path.startswith("/mnt/Projects/dst"):
    #     return os.path.join(
    #         "/mnt/Projects/dst",
    #         "colour",
    #         "latest",
    #         "dis.cube"
    #     )
    return None


def get_show_lut_from_path(path):
    return _path_get_show_lut_from_path(path)


def get_shot_lut_from_path(path):
    return _path_get_shot_lut_from_path(path)
