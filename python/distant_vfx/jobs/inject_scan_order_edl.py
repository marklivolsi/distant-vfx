import csv
import os
import traceback

from ..filemaker import CloudServerWrapper
from ..constants import FMP_URL, FMP_USERNAME, FMP_PASSWORD, FMP_EDIT_DB, FMP_ADMIN_DB, \
    FMP_SCANS_LAYOUT, FMP_IMAGES_LAYOUT, FMP_PROCESS_IMAGE_SCRIPT, LEGAL_THUMB_EXTENSIONS
from . import edl_lowercase_loc


class smpteTC:  # Class for dealing SMPTE Timecode
    def __init__(self, tc, fps):
        if _validTC(tc):
            self.tc = tc  # Store timecode
            self.fps = fps  # Store framerate
            self.frame = int(round(
                (int(tc[:2]) * 3600 + int(tc[3:5]) * 60 + int(tc[6:8])) * fps + int(tc[9:])))  # Store frame number

    def __repr__(self):
        return self.tc


def _listIndices(string, sub):  # Function that returns a list indices for a substring in a string
    return [i for i, n in enumerate(string) if n == sub]  # return the list of found indices


def _validTC(tc):  # Function to validate timecode format, returns boolean
    if len(tc) == 11 or tc.count(":") == 3:  # Validating that it's timecode - could add check for digits
        return 1


def _printDict(events):  # primarily for testing
    print("*****************************************")
    for idx, event in enumerate(events):
        print(idx, event)
    print("*****************************************")


def _edl2dict(ifile, fps=24):  # Script expects an edl file, returns dictionary
    assert os.path.exists(ifile), "I did not find the file at, " + str(ifile)  # Error control
    edl = open(ifile, "r", encoding="utf-8")  # import edl as utf-8 to fix edl's weird formatting
    info = {'EDLfilename': os.path.basename(ifile)}  # Create infor variable and start with fileanme
    events = []  # A list of events in the EDL
    events.append({})  # The first dictionary of an event)
    lines = []  # A list of lines
    i = 0  # Starting a counter
    event_num = 0
    info['ScanOrder'] = int(
        ''.join(i for i in info['EDLfilename'].split("_")[0] if i.isdigit()))  # Set Scan order ID from filename
    # Walk through EDL and poplute Data, NEED TO MAKE DICTIONARY OR CLASS
    for line in edl:
        lines.append(line.split())  # Split Line into section off whitespace
        # Edit Event Line
        if lines[i][0].isdigit():  # Test to see if first data block is a number, assume it's event if so
            event_num = int(lines[i][0])  # Set the event number, will link to list
            events.append({'ScanOrder': info['ScanOrder']})  # Set Dicitionary with the event number
            del lines[i][0]  # Remove the line element of the event number
            # Find timecode with in list of elements
            tcLocation = []  # Create an empty variable timecode locations
            colons = (_listIndices(line, ":"))  # Count the colons
            for j in range(len(colons) - 2):
                if colons[j] + 3 == colons[j + 1] and colons[j + 1] + 3 == colons[
                    j + 2]:  # Use the space between colons to deteremine if they are timecode
                    tcLocation.append(colons[j] - 2)
            # Populate the timecodes into the dictionary
            events[event_num].update({'TimeCodeStart': str(smpteTC(line[tcLocation[0]:tcLocation[0] + 11], fps)),
                                      # Using timecode class into dictionary for each value
                                      'TimeCodeEnd': str(smpteTC(line[tcLocation[1]:tcLocation[1] + 11], fps)),
                                      'SourceStart': int(smpteTC(line[tcLocation[0]:tcLocation[0] + 11], fps).frame),
                                      # Using timecode class into dictionary for each value
                                      'SourceEnd': int(smpteTC(line[tcLocation[1]:tcLocation[1] + 11], fps).frame),
                                      })

            events[event_num].update(
                {'Duration': (int(events[event_num]['SourceEnd']) - int(events[event_num]['SourceStart']))})

            events[event_num].update(
                {'ScanStart': 1001,  # Set the scan start frome TODO Make this come from a config file
                 'ScanEnd': 1000 + events[event_num]['Duration']
                 # Set the scan end frome TODO Make this come from a config file (subtract 1)
                 })

            # Remove timecodes from list of elements.
            trash = []  # Estabish trach variable
            for k, part in enumerate(lines[i]):  # Walk through the elements of the line and check for timecode
                if _validTC(part): trash.append(k)
            del lines[i][trash[0]:]  # Take out the trash!
            del trash[:]  # Take out the trash can!
            # Now that the trash is taken out, we can get back to populating!
            try:  # popuale the Media into the Dictionary
                if len(lines[i]) == 0:
                    events[event_num].update({'Media': str(lines[i][0])})
            except:
                pass  # TODO Need to debug more
        elif line[:1] == '*':  # Additional info, Source File, Locator, Clip Name, etc.
            if line[:16] == "*FROM CLIP NAME:":  # Check for Clipname
                events[event_num].update(
                    {'ClipName': " ".join(str(line[18:]).split())})  # Populate a non white space version of the string
            elif line[:5] == "*LOC:":  # Check for Locator Block
                if len(lines[i]) >= 4:
                    events[event_num].update(
                        {'Filename': str(lines[i][3])})  # Populate Locator Name
            elif line[:8] == "*ASC_SOP":  # Check for CDL Values
                events[event_num].update(
                    {'CDL': " ".join(str(line[8:]).split())})  # Populate a non white space version of the string
            elif line[:8] == "*ASC_SAT":  # Check for ASC Saturation
                events[event_num].update(
                    {'Saturation': " ".join(str(line[8:]).split())})  # Populate a non white space version of the string
            elif line[:13] == "*SOURCE FILE:":  # Check for ASC Saturation
                events[event_num].update({'Source': " ".join(
                    str(line[13:]).split())})  # Populate a non white space version of the string
        i += 1  # Graduate Counter

    for i, event in enumerate(events):
        try:
            events[i].update({'VFXID': event['Filename'].split("_")[0],
                                      'VFXEditorialShots::SCAN': 1,  # turned off, can't import this field
                                      })

        except:
            pass

        # Set VFX ID based on Locator Name
        # if events[]
        # Set Frame Numbers based on timecode

        # Set shot as scanned

    events = list(filter(None, events))

    return events


def _dict2csv(events, csv_filename):  # export csv from dictionary NEED TO RENAME VARIABLES TO BE LESS EDL BASED
    eventsKeys = []  # Create blank list to enumerate the event keys into
    for idx, event in enumerate(events):  # This is case different events have difference data sets
        eventsKeys.extend(event.keys())  # Create a large list of all the event keys
    fields = sorted(set(eventsKeys))  # Removing duplicates by passing through variable types
    with open(csv_filename, 'w') as output:  # Opening File for csv writing
        csv_out = csv.DictWriter(output, fieldnames=fields,
                                 dialect='excel')  # prepping the csv for input! using excel style
        csv_out.writeheader()
        for idx, event in enumerate(events):  # Walk through events and pass it to the csv
            csv_out.writerow(event)


def _inject_scan_edl(edl_dict):
    with CloudServerWrapper(url=FMP_URL,
                            user=FMP_USERNAME,
                            password=FMP_PASSWORD,
                            database=FMP_EDIT_DB,
                            layout=FMP_SCANS_LAYOUT
                            ) as fmp:
        fmp.login()

        # create scan records
        for line in edl_dict:
            try:
                record_id = fmp.create_record(line)
            except:
                traceback.print_exc()


def _find_stills(root_path):
    for root, dirs, files in os.walk(root_path):
        for filename in files:
            ext = os.path.splitext(filename)[1]
            if ext in LEGAL_THUMB_EXTENSIONS:
                filepath = os.path.join(root, filename)
                yield filename, filepath


def _inject_stills(root_path):
    stills = _find_stills(root_path)
    if not stills:
        return

    with CloudServerWrapper(url=FMP_URL,
                            user=FMP_USERNAME,
                            password=FMP_PASSWORD,
                            database=FMP_ADMIN_DB,
                            layout=FMP_IMAGES_LAYOUT
                            ) as fmp:
        fmp.login()
        for still in stills:
            image_did_upload = False
            try:
                filename, filepath = still[0], still[1]
                record_data = {'Filename': filename}
                record_id = fmp.create_record(record_data)
                file = open(filepath, 'rb')
                image_did_upload = fmp.upload_container(record_id, field_name='Image', file_=file)
                file.close()
            except:
                traceback.print_exc()

            if image_did_upload:
                try:
                    image_record = fmp.get_record(record_id)
                    primary_key = image_record.PrimaryKey
                    script_result = fmp.perform_script(FMP_PROCESS_IMAGE_SCRIPT, param=primary_key)
                except:
                    traceback.print_exc()


def main(edl_path, csv_out=False, inject_stills=False):
    edl_lowercase_loc.main(edl_path)
    edl_dict = _edl2dict(edl_path)
    if not csv_out:
        _inject_scan_edl(edl_dict)
        if inject_stills:
            root_path = os.path.dirname(edl_path)
            _inject_stills(root_path)
    else:
        csv_path = edl_path.rsplit('.', 1)[0] + '.csv'
        _dict2csv(edl_dict, csv_path)
