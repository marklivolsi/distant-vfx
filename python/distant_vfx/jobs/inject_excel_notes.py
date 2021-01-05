from ..filemaker import CloudServerWrapper
from ..parsers import ExcelNotesParser
from ..constants import FMP_URL, FMP_USERNAME, FMP_PASSWORD, FMP_VFX_DB, FMP_NOTES_LAYOUT


def main(xlsx_path):
    parser = ExcelNotesParser()
    parser.read_xlsx(xlsx_path)
    xlsx_rows = parser.get_rows_as_dicts()

    fmp_records = []
    for row in xlsx_rows:
        note_record = {
            'Versions_Notes::Vendor': row['vendor'],
            'VFXID': row['shot or asset id'],
            'Filename': row['filename'],
        }

        # create prod note dict
        prod_note = row['prodNote']
        if prod_note:
            note_record['Note'] = prod_note
            fmp_records.append(note_record)

        # create edit note dict
        edit_note = row['send to editorial?']
        if edit_note:
            edit_note = f'send to editorial: {edit_note}'
            note_record['Note'] = edit_note
            fmp_records.append(note_record)

    with CloudServerWrapper(url=FMP_URL,
                            user=FMP_USERNAME,
                            password=FMP_PASSWORD,
                            database=FMP_VFX_DB,
                            layout=FMP_NOTES_LAYOUT
                            ) as fmp:
        fmp.login()
        for record in fmp_records:
            try:
                fmp.create_record(record)
                print(f'Note record created (data: {record})')
            except Exception as e:
                print(e)
