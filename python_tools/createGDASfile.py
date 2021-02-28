import numpy as np
from icecube import dataclasses, dataio
from icecube.dataclasses import I3Time
import subprocess


def isFileExists(runID, eventID):
    filename = "/data/user/rturcotte/corsika_simulation/atmosphere/atmos_runId{0}_eventId{1}.txt".format(runID, eventID)
    if filename return True
    else return False

def createEmptyGDASFile(runID, eventID):
    f = open("/data/user/rturcotte/corsika_simulation/atmosphere/atmos_runId{0}_eventId{1}.txt".format(runID, eventID), "w+")
    return f.name

def runGDAS(runID, eventID, unixTime):
    if isFileExist(runID, eventID):
        print("the file exists already for runID{0}, eventID{1}".format(runID, eventID))
    else:
        filename = createEmptyGDASFile(runID, eventID)
        unixTime = str(unixTime)
        print(runID, eventID, unixTime)
        print(filename)
        subprocess.run(["python", "/data/user/rturcotte/corsika/corsika-77401/src/utils/gdastool", "--observatory", "icetop", "-o", filename, "-t", unixTime])
        
def getShowerIdentification(filename):
    in_file = dataio.I3File(filename, 'r')
    for frame in in_file:
        runID = frame['I3EventHeader'].run_id
        eventID = frame['I3EventHeader'].event_id
        utcTime = frame['I3EventHeader'].start_time
        unixTime = utcTime.unix_time
    return runID, eventID, unixTime

def runAllGDASforOneFile(filename):
    in_file = dataio.I3File(filename, 'r')
    for frame in in_file:
        utcTime = frame['I3EventHeader'].start_time
        unixTime = utcTime.unix_time
        runGDAS(frame['I3EventHeader'].run_id, frame['I3EventHeader'].event_id, unixTime)

#getShowerIdentification("/data/user/rturcotte/showers/showers_12112020.i3.gz")
filename = "/data/user/rturcotte/showers/showers_12112020.i3.gz"
runAllGDASforOneFile(filename)







