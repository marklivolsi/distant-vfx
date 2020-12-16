import csv
import datetime
from logging import captureWarnings
import os
import re
import time
from fmrest import CloudServer
from fmrest.exceptions import BadJSON
from ..constants import FMP_URL, FMP_USERNAME, FMP_PASSWORD, FMP_EDIT_DB, FMP_CUTHISTORY_LAYOUT, FMP_CUTHISTORYSHOTS_LAYOUT


class smpteTC:  # Class for dealing SMPTE Timecode
    def __init__(self, tc, fps):
        if _validTC(tc):
            self.tc = tc  # Store timecode
            self.fps = fps  # Store framerate
            self.frame = int(round(
                (int(tc[:2]) * 3600 + int(tc[3:5]) * 60 + int(tc[6:8])) * fps + int(tc[9:])))  # Store frame number

    def __repr__(self):
        return self.tc


def listIndices(string, sub):  # Function that returns a list indices for a substring in a string
    return [i for i, n in enumerate(string) if n == sub]  # return the list of found indices


def _validTC(tc):  # Function to validate timecode format, returns boolean
    if len(tc) == 11 or tc.count(":") == 3:  # Validating that it's timecode - could add check for digits
        return 1


def _printDict(events):  # primarily for testing
    for event in events:
        for key, value in event.items():
            if key == "Event":
                print("|----Event:" + str(value))
            else:
                print(key + "\t" + str(value))


def _edl2dict(ifile, fps=24):  # Script expects an edl file, returns dictionary
    assert os.path.exists(ifile), "I did not find the file at, " + str(ifile)  # Error control
    edl = open(ifile, "r", encoding="utf-8")  # import edl as utf-8 to fix edl's weird formatting

    # Setting some variables
    info = {'filename': os.path.basename(ifile),
            'edlBase': os.path.basename(ifile).split(".")[0],
            }

    events = []  # A list of events in the EDL
    events.append({})  # The first dictionary of an event)
    lines = []  # A list of lines
    i = 0
    event_num = 0

    # Walk through EDL and poplute Data, NEED TO MAKE DICTIONARY OR CLASS
    for line in edl:
        lines.append(line.split())  # Split Line into section off whitespace
        # Edit Event Line
        if lines[i][0].isdigit():  # Test to see if first data block is a number, assume it's event if so
            event_num = int(lines[i][0])  # Set the event number, will link to list
            events.append({'Event': event_num})  # Set Dicitionary with the event number
            del lines[i][0]  # Remove the line element of the event number
            # Find timecode with in list of elements
            tcLocation = []  # Create an empty variable timecode locations
            colons = (listIndices(line, ":"))  # Count the colons
            for j in range(len(colons) - 2):
                if colons[j] + 3 == colons[j + 1] and colons[j + 1] + 3 == colons[
                    j + 2]:  # Use the space between colons to deteremine if they are timecode
                    tcLocation.append(colons[j] - 2)
            # Populate the timecodes into the dictionary

            events[event_num].update({'ReelVersion': info['edlBase']})

            events[event_num].update({'SourceInTC': str(smpteTC(line[tcLocation[0]:tcLocation[0] + 11], fps)),
                                      # Using timecode class into dictionary for each value
                                      'SourceOutTC': str(smpteTC(line[tcLocation[1]:tcLocation[1] + 11], fps)),
                                      'SeqInTC': str(smpteTC(line[tcLocation[2]:tcLocation[2] + 11], fps)),
                                      'SeqOutTC': str(smpteTC(line[tcLocation[3]:tcLocation[3] + 11], fps)),
                                      'SourceInF': int(smpteTC(line[tcLocation[0]:tcLocation[0] + 11], fps).frame),
                                      # Using timecode class into dictionary for each value
                                      'SourceOutF': int(smpteTC(line[tcLocation[1]:tcLocation[1] + 11], fps).frame),
                                      'SeqInF': int(smpteTC(line[tcLocation[2]:tcLocation[2] + 11], fps).frame),
                                      'SeqOutF': int(smpteTC(line[tcLocation[3]:tcLocation[3] + 11], fps).frame),
                                      })

            events[event_num].update(
                {'Duration': (int(events[event_num]['SeqOutF']) - int(events[event_num]['SeqInF']))})

            # Remove timecodes from list of elements.
            trash = []  # Estabish trach variable
            for k, part in enumerate(lines[i]):  # Walk through the elements of the line and check for timecode
                if _validTC(part): trash.append(k)
            del lines[i][trash[0]:]  # Take out the trash!
            del trash[:]  # Take out the trash can!

            # popuale the Media into the Dictionary
            try:
                if len(lines[i]) == 0:
                    events[event_num].update({'Media': str(lines[i][0])})
            except:
                pass  # Need to debug more
        elif line[:1] == '*':  # Additional info, Source File, Locator, Clip Name, etc.
            if line[:16] == "*FROM CLIP NAME:":  # Check for Clipname
                events[event_num].update(
                    {'Clip': " ".join(str(line[18:]).split())})  # Populate a non white space version of the string
            elif line[:14] == "*TO CLIP NAME:":
                events[event_num].update({'Effect': "Disolve"})  # Populate a non white space version of the string
            elif line[:5] == "*LOC:":  # Check for Locator
                events[event_num].update(
                    {'LocatorTC': str(smpteTC(lines[i][1], fps)),  # Using timecode class for Locator Timecode
                     'LocatorColor': str(lines[i][2]),  # Popualting Locator Color
                     })
                if len(lines[i]) >= 4:
                    events[event_num].update(
                        {'Locator': str(lines[i][3])})  # Populate Locator Name
            elif line[:13] == "*SOURCE FILE:":  # Check for ASC Saturation
                events[event_num].update({'Source': " ".join(
                    str(line[13:]).split())})  # Populate a non white space version of the string
            # elif line.count(":") >= 1:                                                              #Search for unknown Notes
            # events[event_num].update( { str(line[1:line.index(":")]) :" ".join(str(line[line.index(":"):]).split()) } )           #Populate a non white space version of the string
            # THIS WILL BE FIXED WHEN I GET SPEED CHANGES TO TEST -----------------------------------------------
        elif lines[i][0] == 'M2':  # Test if it's a Speed Effect
            new = {'Effect': 'Respeed',  # Populating dictionary using hard codded spacing
                   'EffectMedia': lines[i][1],
                   'EffectFPS': float(lines[i][2].strip()),
                   'EffectStart': lines[i][3],
                   }
            events[event_num].update(new)  # Merging Dictionaries
            # ---------------------------------------------------------------------------------------------------


        else:  # Catch all for anything unrecognized
            events[event_num].update({'Text': " ".join(str(line).split())})  # injecting the unknown as text
        i += 1  # Graduate Counter
    events = list(filter(None, events))
    return events


def _dict2csv(events, csv_filename):  # export csv from dictionary NEED TO RENAME VARIABLES TO BE LESS EDL BASED
    eventsKeys = []  # Create blank list to enumerate the event keys into
    for idx, event in enumerate(events):  # This is case different events have difference data sets
        eventsKeys.extend(event.keys())  # Create a large list of all the event keys
    fields = sorted(set(eventsKeys))  # Removing duplicates by passing through variable types
    with open(csv_filename, 'w') as output:  # Opening File for csv writing
        csv_out = csv.DictWriter(output, fieldnames=fields,
                                 dialect='excel')  # Prepiing the csv for input! using excel style
        csv_out.writeheader()
        for idx, event in enumerate(events):  # Walk through events and pass it to the csv
            csv_out.writerow(event)


def _versionImport(reel_version):
    reelInfo = {'ReelVersion': reel_version,  # Create dictionary, starting with Reel info
                'ACTIVE': 1
                }
    breakOut = reel_version.split("_")  # breakout components of the name
    for chunk in breakOut:  # Walk through parts of the breakout
        if chunk.lower().count('r'):  # Look for R in chunk of filename
            reelInfo.update({'Reel': int(re.sub('[^0-9]', '', chunk))})  # Create Reel in dictionary
        elif chunk.isdigit() and len(chunk) == 8:  # Look for 8 digits, hope they are a date!
            reelInfo.update({'Date': datetime.date(int(chunk[0:4]), int(chunk[4:6]), int(chunk[-2:])).strftime(
                "%m/%d/%y")})  # Create the Date in a filemaker friendly format
    return reelInfo


def _inject_reel(edl_dict, reel_dict, tries=3):
    with CloudServer(
        url=FMP_URL,
        user=FMP_USERNAME,
        password=FMP_PASSWORD,
        database=FMP_EDIT_DB,
        layout=FMP_CUTHISTORYSHOTS_LAYOUT
    ) as fmp:
        fmp.login()

        # Import event records
        for line in edl_dict:
            for i in range(tries):
                try:
                    record_id = fmp.create_record(line)
                except BadJSON as e:
                    if i <= tries - 1:
                        time.sleep(0.5)
                        continue
                    else:
                        print(f'Error: {e} \n Response: {e._response}')
                        break
                except Exception as e:
                    print(e)
                    break
                else:
                    break

        # Import reel record
        fmp.layout = FMP_CUTHISTORY_LAYOUT
        for i in range(tries):
            try:
                record_id = fmp.create_record(reel_dict)
            except BadJSON as e:
                if i <= tries - 1:
                    time.sleep(0.5)
                    continue
                else:
                    print(f'Error: {e} \n Response: {e._response}')
                    break
            except Exception as e:
                print(e)
                break
            else:
                break


def main(edl_path, csv_out=False):
    captureWarnings(True)
    edl_dict = _edl2dict(edl_path)
    reel_dict = _versionImport(edl_dict[1]["ReelVersion"])
    if not csv_out:
        _inject_reel(edl_dict, reel_dict)
    else:
        csv_path = edl_path.rsplit('.', 1)[0] + '.csv'
        _dict2csv(edl_dict, csv_path)
    print("Reel imported into database successfully.")
