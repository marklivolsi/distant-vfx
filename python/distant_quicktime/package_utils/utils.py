import datetime
import os


PREFIX = "/mnt/Projects/dst/mailbox"
EDIT_VENDOR_NAME = "edt"
INTERNAL_MAILBOX_TEMPLATE = "{direction}_{vendor}"
MAILBOX_PACKAGE_NAME_TEMPLATE_BASE = "{vendor}_{source_vendor}_{date}_%s"

def directory_is_larger_than(directory, maxsize):
    # Not implemented
    return False


def _build_internal_mailbox_name(direction="to", vendor=None):
    if direction not in ("to", "fr"):
        raise ValueError("direction kwarg must be one of (\"to\", \"fr\")")
    if vendor is None:
        raise ValueError("vendor kwarg must not be None")
    return INTERNAL_MAILBOX_TEMPLATE.format(direction=direction, vendor=vendor)


def _find_next_package_letter_name(directory, base_name, maxsize=None):
    for x in range(97, 123):
        # a - z
        finalized_package_name = base_name % chr(x)
        path = os.path.join(directory, finalized_package_name)
        if os.path.exists(path):
            if maxsize:
                if directory_is_larger_than(path, maxsize):
                    continue
                # Directory has room
                return finalized_package_name
    return None

def _build_mailbox_package_name(directory, vendor, source_vendor, date, maxsize=None):
    base_package_name = MAILBOX_PACKAGE_NAME_TEMPLATE_BASE.format(
        vendor=vendor,
        source_vendor=source_vendor,
        date=date,
    )
    package_letter_name = _find_next_package_letter_name(directory, base_package_name, maxsize=maxsize)
    if package_letter_name:
        return package_letter_name

    # There are already 26 for today.
    for x in range(97, 123):
        # a - z
        base_package_name = base_package_name % chr(x) + "%s"
        package_letter_name = _find_next_package_letter_name(
            directory,
            base_package_name,
            maxsize=maxsize
        )
        if package_letter_name:
            return package_letter_name
    # If we get to here, we need more than 2 digits for letters...And something is probably wrong.
    raise ValueError("Could not find suitable packagename in 2 alphanumeric bytes. Confirm that things aren't weird")


def get_or_create_edit_package_directory(direction="to", source_vendor="dst", date=None):
    if direction not in ("to", "fr"):
        raise ValueError("direction kwarg must be one of (\"to\", \"fr\")")
    if date is None:
        date = datetime.date.today().strftime("%Y%m%d")

    base_directory = os.path.join(
        PREFIX,
        EDIT_VENDOR_NAME,
        _build_internal_mailbox_name(
            direction=direction, vendor=EDIT_VENDOR_NAME
        ),
    )
    package_directory = os.path.join(
        base_directory,
        _build_mailbox_package_name(
            base_directory,
            vendor=EDIT_VENDOR_NAME, source_vendor=source_vendor, date=date
        )
    )

    if not os.path.exists(package_directory):
        os.makedirs(package_directory)
    return package_directory
