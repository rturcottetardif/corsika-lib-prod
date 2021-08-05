#!/usr/bin/python3

import numpy as np
import subprocess
from python_tools import FileHandler

handler = FileHandler.FileHandler()
# atmosDir = "/data/user/rturcotte/corsika-library-production/atmosphere"


def isFileExists(runID, eventID):
    import os.path
    filename = handler.atmosdir + "/atmos_runId{0}_eventId{1}.txt".format(runID, eventID)
    if os.path.isfile(filename):
        return True
    else:
        return False


def createEmptyGDASFile(runID, eventID):
    f = open(handler.atmosdir + "/atmos_runId{0}_eventId{1}.txt".format(runID, eventID), "w+")
    return f.name


def runGDAS(runID, eventID, unixTime):
    if isFileExists(runID, eventID):
        print("the file already exists for runID{0}, eventID{1}".format(runID, eventID))
    else:
        filename = createEmptyGDASFile(runID, eventID)
        unixTime = str(unixTime)
        print(runID, eventID, unixTime)
        subprocess.run(["python", handler.corsikadir[:-4] + "/src/utils/gdastool", "--observatory", "icetop", "-o", filename, "-t", unixTime])


def getShowerIdentification(frame):
    runID = frame['I3EventHeader'].run_id
    eventID = frame['I3EventHeader'].event_id
    unixTime = frame['TaxiTime'].unix_time
    return runID, eventID, unixTime


def runForNpy(filename):
    with open(filename, 'rb') as f:
        try:
            while 1:
                event = np.load(f)
                runGDAS(event["runId"], event["eventId"], event["time"])
        except ValueError:     #Sketchy fix
            print("EoF : ", filename)


def runAllGDASforOneFile(filename):
    print("making GDAS file for all events in :", filename)
    if ".i3.gz" in filename:
        from icecube import dataio
        in_file = dataio.I3File(filename, 'r')
        for frame in in_file:
            runId, eventId, unixTime = getShowerIdentification(frame)
            runGDAS(runId, eventId, unixTime)
    elif ".npy" in filename:
        runId, eventId, unixTime = runForNpy(filename)
        runGDAS(runId, eventId, unixTime)


if __name__ == '__main__':
    filenameNPY = handler.basedir + "/resources/exampleShowerlist.npy"
    runAllGDASforOneFile(filenameNPY)


