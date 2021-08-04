#!/usr/bin/python3

import numpy as np
from icecube import dataclasses, dataio
from icecube.dataclasses import I3Time
import subprocess
# from . import FileHandler

# # that doesn't work!!! importation problem
# handler = FileHandler.FileHandler()
atmosDir = "/data/user/rturcotte/corsika-library-production/atmosphere"


def isFileExists(runID, eventID):
    import os.path
    filename = atmosDir + "/atmos_runId{0}_eventId{1}.txt".format(runID, eventID)
    if os.path.isfile(filename):
        return True
    else:
        return False


def createEmptyGDASFile(runID, eventID):
    f = open(atmosDir + "/atmos_runId{0}_eventId{1}.txt".format(runID, eventID), "w+")
    # f = open(handler.atmosdir + "atmos_runId{0}_eventId{1}.txt".format(runID, eventID))
    return f.name


def runGDAS(runID, eventID, unixTime):
    if isFileExists(runID, eventID):
        print("the file already exists for runID{0}, eventID{1}".format(runID, eventID))
    else:
        filename = createEmptyGDASFile(runID, eventID)
        unixTime = str(unixTime)
        print(runID, eventID, unixTime)
        print(filename)
        subprocess.run(["python", "/data/user/rturcotte/corsika/corsika-77401/src/utils/gdastool", "--observatory", "icetop", "-o", filename, "-t", unixTime])


def getShowerIdentification(frame):
    # in_file = dataio.I3File(filename, 'r')
    # for frame in in_file:
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
        except ValueError: #Sketchy fix
            print("EoF : ", filename)


def runAllGDASforOneFile(filename):
    if filename.split(".")[-1] == ".i3.gz":
        in_file = dataio.I3File(filename, 'r')
        for frame in in_file:
            runId, eventId, unixTime = getShowerIdentification(frame)
            runGDAS(runId, eventId, unixTime)
    elif filename.split(".")[-1] == ".npy":
        runId, eventId, unixTime = runForNpy(filename)
        runGDAS(runId, eventId, unixTime)


if __name__ == '__main__':
    #getShowerIdentification("/data/user/rturcotte/showers/showers_12112020.i3.gz")
    path = "/data/user/rturcotte/showers/"
    filename_clear = "showersV4_20210217_clear.i3.gz"
    filename_coinc = "showersV4_coinc_20210217.i3.gz"
    filenameNPY =
    runAllGDASforOneFile(filenameNPY)






