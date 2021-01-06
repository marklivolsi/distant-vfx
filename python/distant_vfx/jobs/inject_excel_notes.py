import traceback
from copy import deepcopy
from ..filemaker import CloudServerWrapper
from ..parsers import ExcelNotesParser
from ..utilities import dict_items_to_str
from ..constants import FMP_URL, FMP_USERNAME, FMP_PASSWORD, FMP_VFX_DB, FMP_NOTES_LAYOUT


def main(xlsx_path):
    parser = ExcelNotesParser()
    parser.read_xlsx(xlsx_path)
    xlsx_rows = parser.get_rows_as_dicts()

    fmp_records = []
    for row in xlsx_rows:
        note_record = _create_base_note_record_dict(row)

        # create prod note dict
        prod_note = row.get('prodNote')
        if prod_note:
            note_record['Note'] = prod_note
            fmp_records.append(note_record)

        # create edit note dict
        edit_note = row.get('to editorial?')
        if edit_note:
            edit_note = f'send to editorial: {edit_note}'
            edit_note_record = deepcopy(note_record)
            edit_note_record['Note'] = edit_note
            fmp_records.append(edit_note_record)

        # create comp note dict
        comp_note = row.get('to comp?')
        if comp_note:
            comp_note_record = deepcopy(note_record)
            comp_note = f'cut into comp: {comp_note}'
            comp_note_record['Note'] = comp_note
            fmp_records.append(comp_note_record)

    # Inject notes to filemaker
    with CloudServerWrapper(url=FMP_URL,
                            user=FMP_USERNAME,
                            password=FMP_PASSWORD,
                            database=FMP_VFX_DB,
                            layout=FMP_NOTES_LAYOUT
                            ) as fmp:
        fmp.login()
        for record in fmp_records:
            try:
                record_id = fmp.create_record(record)
                print(f'Note record created (data: {record})')
            except:
                traceback.print_exc()


@dict_items_to_str
def _create_base_note_record_dict(xlsx_row):
    note_record = {
        'VFXID': xlsx_row.get('shot or asset id'),
        'Filename': xlsx_row.get('filename'),
    }
    return note_record
