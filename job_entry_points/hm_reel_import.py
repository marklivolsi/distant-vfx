#!/usr/bin/env python3

# MODULES
import sys  # Need to bring in the argument
import os  # Need to check if file path is legit
import io  # Need to output file
import csv  # Need to format and output CSV
# import fmrest  # Need to post EDL info to Database
import logging  # Need to capture errors and not annoy user
import requests  # Need to hide ssl warnings
# import mac_tag  # So I can add tags to folders, etc.
import datetime
import re

# Updates to use FM Cloud Instead
from python.distant_vfx.config import Config
from distant_vfx.filemaker import FMCloudInstance

FMP_URL = os.environ['FMP_URL']
FMP_USERPOOL = os.environ['FMP_USERPOOL']
FMP_CLIENT = os.environ['FMP_CLIENT']
FMP_USERNAME = os.environ['FMP_USERNAME']
FMP_PASSWORD = os.environ['FMP_PASSWORD']
FMP_EDIT_DB = os.environ['FMP_EDIT_DB']
FMP_LAYOUT_CUTHISTORY = os.environ['FMP_LAYOUT_CUTHISTORY']
FMP_LAYOUT_CUTHISTORYSHOTS = os.environ['FMP_LAYOUT_CUTHISTORYSHOTS']



# CLASSES
class smpteTC:  # Class for dealing SMPTE Timecode
    def __init__(self, tc, fps):
        if validTC(tc):
            self.tc = tc  # Store timecode
            self.fps = fps  # Store framerate
            self.frame = int(round(
                (int(tc[:2]) * 3600 + int(tc[3:5]) * 60 + int(tc[6:8])) * fps + int(tc[9:])))  # Store frame number

    def __repr__(self):
        return self.tc

    # FUNCTIONS


def listIndices(string, sub):  # Function that returns a list indices for a substrign in a string
    return [i for i, n in enumerate(string) if n == sub]  # return the list of found indices


def validTC(tc):  # Function to validate timecode format, returns boolean
    if len(tc) == 11 or tc.count(":") == 3: return 1  # Validating that it's timecode - could add check for digits


def printDict(events):  # primarily for testing
    # fields = set()
    for event in events:
        for key, value in event.items():
            # fields.add(key)
            if key == "Event":
                print("|----Event:" + str(value))
            else:
                print(key + "\t" + str(value))
    # rint(fields)


def edl2dict(ifile, fps=24):  # Script expects an edl file, returns dictionary
    assert os.path.exists(ifile), "I did not find the file at, " + str(ifile)  # Error control
    edl = io.open(ifile, "r", encoding="utf-8")  # import edl as utf-8 to fix edl's weird formatting

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
                if validTC(part): trash.append(k)
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


def dict2csv(events, csv_filename):  # export csv from dictionary NEED TO RENAME VARIABLES TO BE LESS EDL BASED
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


def versionImport(ReelVersion):
    # fms = fmrest.Server(  # setup server dictionary, move address, user and password to config
    #     'https://192.168.103.5',
    #     user='vfx_python',
    #     password='79a142f6-519d-4e54-aa63-2b7059f8e1cf',
    #     database='VFXEditorial',
    #     layout='api_cuthistory',
    #     verify_ssl=False  # if you are testing without cert/domain you may need the parameter verify_ssl=False here.
    # )
    reelInfo = {'ReelVersion': ReelVersion,  # Create dictionary, starting with Reel info
                'ACTIVE': 1
                }
    breakOut = ReelVersion.split("_")  # breakout components of the name
    for chunk in breakOut:  # Walk through parts of the breakout
        if chunk.lower().count('r'):  # Look for R in chunk of filename
            reelInfo.update({'Reel': int(re.sub('[^0-9]', '', chunk))})  # Create Reel in dicitonary
        elif chunk.isdigit() and len(chunk) == 8:  # Look for 8 digits, hope they are a date!
            reelInfo.update({'Date': datetime.date(int(chunk[0:4]), int(chunk[4:6]), int(chunk[-2:])).strftime(
                "%m/%d/%y")})  # Create the Date in a filemaker freindly format
    # fms.login()  # log into filemaker
    # if 'Reel' in reelInfo:
    #     foundset = fms.find([{'Reel': reelInfo['Reel']}])
    #     for record in foundset:
    #         if record.ACTIVE:
    #             record.ACTIVE = 0
    #             record.PREVIOUS = 1
    #             fms.edit(record)
    #         elif record.PREVIOUS:
    #             record.PREVIOUS = 0
    #             fms.edit(record)
    # fms.create_record(reelInfo)  # send ReelVersion of EDL info to filemaker

    return reelInfo


# def reelImport(edlDict):
#     fms = fmrest.Server(  # setup server dictionary, move address, user and password to config
#         'https://192.168.103.5',
#         user='vfx_python',
#         password='79a142f6-519d-4e54-aa63-2b7059f8e1cf',
#         database='VFXEditorial',
#         layout='api_cuthistoryshots',
#         verify_ssl=False  # if you are testing without cert/domain you may need the parameter verify_ssl=False here.
#     )
#     fms.login()  # log into filemaker
#     for line in edlDict:  # Walk through EDL dictionary
#         fms.create_record(line)  # send lines of EDL info to filemaker




# SCRIPT (ALWAYS EXECUTES)
if __name__ == "__main__":
    # requests.packages.urllib3.disable_warnings()  # To hide ssl warnings
    logging.captureWarnings(1)  # capture warnings so the user doesnt have to see them
    edl_file = str(sys.argv[1]).strip()  # import System argument
    reelEDL = edl2dict(edl_file)  # Create a dictionary from the edl
    # printDict(reelEDL)
    # reelImport(reelEDL)  # import the reel into the database
    reel_info = versionImport(reelEDL[1]["ReelVersion"])  # import the reel version into the database

    with FMCloudInstance(FMP_URL,
                         FMP_USERNAME,
                         FMP_PASSWORD,
                         FMP_EDIT_DB,
                         FMP_USERPOOL,
                         FMP_CLIENT) as fmp:
        # Import shot records
        for line in reelEDL:
            fmp.new_record(FMP_LAYOUT_CUTHISTORYSHOTS, data=line)

        # Import reel record
        fmp.new_record(FMP_LAYOUT_CUTHISTORY, data=reel_info)

    # TODO: Kick off fmp script to make older reels inactive

    print("\nData imported into Database sucessfully")
    # mac_tag.add("red", edl_file)