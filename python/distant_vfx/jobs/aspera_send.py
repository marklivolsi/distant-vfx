import traceback
import subprocess
import os
import yagmail
from ..aspera import AsperaCLI
from ..constants import EMAIL_USERNAME, EMAIL_PASSWORD


def main(user,
         password,
         url,
         package_id_json_file,
         url_prefix,
         filepath,
         recipients,
         title,
         vendor,
         note=None,
         content_protect_password=None,
         cc_on_download=None,
         cc_on_upload=None,
         email=None):

    aspera = AsperaCLI(
        user=user,
        password=password,
        url=url,
        package_id_json_file=package_id_json_file,
        url_prefix=url_prefix
    )

    try:
        aspera.send_package(filepath=filepath,
                            recipients=recipients,
                            title=title,
                            note=note,
                            content_protect_password=content_protect_password,
                            cc_on_download=cc_on_download,
                            cc_on_upload=cc_on_upload)
    except:
        traceback.print_exc()
    else:
        print(f'Sent package {title}')

    if email:
        package_name = os.path.basename(filepath)
        tree = _get_package_tree(filepath)
        subject = f'[Distant] VFX Delivery - {package_name}'
        content = _build_email_body(
            vendor=vendor,
            package_name=package_name,
            tree=tree,
            note=note
        )
        _send_email(recipients, subject, content)


def _build_email_body(vendor, package_name, tree, note):
    message = f'Hello team {vendor},\n\n' \
              f'Please find the following package uploaded to you via Aspera.\n\n' \
              f'<b><u>Package Name:</u></b>\n' \
              f'{package_name}\n\n'
    if note:
        message += f'<b><u>Note:</u></b>\n' \
                   f'{note}\n\n'
    message += f'<b><u>Contents:</u></b>\n' \
               f'{tree}'
    return message


def _send_email(recipients, subject, content):
    yag = yagmail.SMTP(
        user=EMAIL_USERNAME,
        password=EMAIL_PASSWORD
    )
    yag.send(
        to=recipients,
        subject=subject,
        contents=content
    )


def _get_package_tree(filepath):
    cmd = ['tree', str(filepath)]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=False
    )
    stdout, stderr = process.communicate()
    return stdout


