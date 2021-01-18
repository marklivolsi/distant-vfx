import traceback
from ..aspera import AsperaCLI


def main(user,
         password,
         url,
         package_id_json_file,
         url_prefix,
         filepath,
         recipients,
         title,
         note=None,
         content_protect_password=None,
         cc_on_download=None,
         cc_on_upload=None):

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


