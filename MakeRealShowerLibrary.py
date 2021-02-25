#!/usr/bin/env python3

import os
import subprocess
import pathlib
import numpy as np
import pandas as pd
from python_tools import FileHandler
from icecube import dataio, radcube
from icecube.icetray import I3Frame, I3Units

IdBegin = 0
UseParallel = False
UseStar = False
SendToCondor = False
UseRealAtmos = True

handler = FileHandler.FileHandler()


def GetCluster():

    stdout, stderr = subprocess.Popen(['hostname', '-d'],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT).communicate()

    if "icecube" in str(stdout):
        return "icecube"

    stdout, stderr = subprocess.Popen(['hostname', '-s'],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT).communicate()

    if "asterix" in str(stdout):
        return "asterix"
    elif "login" in str(stdout):
        return "caviness"

    print("YIKES! Who are you? ", str(stdout))
    return "unknown"


class ShowerGroup(object):
    """docstring for ShowerGroup"""

    def __init__(self, runID, eventID, zen, azi, eng, prim, n):
        self.runID = runID
        self.eventID = eventID
        self.zenith = zen
        self.energy = eng  # [PeV]
        self.azimuth = azi
        self.primary = prim
        self.nShowers = n

    def SubmitShowers(self):

        MakeSubFile(self.runID, self.eventID, self.zenith, self.azimuth,
                    self.energy, self.primary, self.nShowers, IdBegin)

        cluster = GetCluster()
        if "caviness" == cluster:
            group = os.environ['WORKGROUP']
            print("Submitting on workgroup", group)

            subprocess.call(["sbatch", "--partition=" +
                             str(group), "tempSubFile.submit"])

        elif "asterix" == cluster:
            subprocess.call(["sbatch", "tempSubFile.submit"])

        elif "icecube" == cluster:
            subprocess.call(["condor_submit", "tempSubFile.submit", "-batch-name",
                             "{0:0.0f}_{1:0.1f}".format(self.zenith, np.log10(self.energy) + 15)])

        # subprocess.call(["rm", "tempSubFile.submit"])


def ShowerString(runID, eventID, zen, azi, eng, prims, n):
    tempList = []
    for prim in prims:
        shwr = ShowerGroup(runID, eventID, zen, azi, eng, prim, n)
        tempList.append(shwr)
    return tempList


def DoThin(peV, zenith):
    return True


def MakeSubFile(runID, eventID, zen, azi, eng, prim, n, id):  # modify here

    print("Making subfile begining with id", IdBegin)
    print("Zen {0}, Eng {1}, azi {2}".format(zen, eng, azi))
    print("runID {0}, eventID {1}".format(runID, eventID))

    file = open("tempSubFile.submit", "w")

    file.write("#!/bin/bash\n")

    logPath = str(handler.logfiledir) + \
        "/realEvents/runID{0}_eventID{1}/".format(runID, eventID)
    pathlib.Path(logPath).mkdir(parents=True, exist_ok=True)

    cluster = GetCluster()
    if "caviness" == cluster or "asterix" == cluster:

        file.write(
            "#SBATCH --job-name={0:0.0f}_{1:0.1f}\n".format(zen, np.log10(eng) + 15))
        file.write("#SBATCH --output={0}log.%a.out\n".format(logPath))
        file.write("#SBATCH --nodes=1\n")

        if "caviness" == cluster:
            file.write("#SBATCH --export=NONE\n")

        if UseParallel:
            file.write("#SBATCH --time=12:00:00\n")
            file.write("#SBATCH --tasks-per-node=6\n")
            file.write("#SBATCH --mem-per-cpu=2000\n")
        else:
            file.write("#SBATCH --time=7-00:00:00\n")
            file.write("#SBATCH --tasks-per-node=1\n")
            file.write("#SBATCH --mem-per-cpu=4096\n")
            if "asterix" == cluster:
                file.write("#SBATCH --partition=long\n")

        file.write("#SBATCH --array=0-{0}\n".format(int(n - 1)))
        file.write("\nSTARTID={0}\n".format(id))
        file.write("ARRAYID=$SLURM_ARRAY_TASK_ID\n")
        file.write("ID=$(($STARTID + $ARRAYID))\n\n")

        file.write("{0}SubmitCtrl.sh ".format(handler.resourcedir))
        file.write("--id $ID ")

    elif "icecube" == cluster:
        file.write("StartIDOffset={0}\n".format(id))
        file.write("ID=$$([$(Process) + $(StartIDOffset)])\n\n\n")

        file.write("Executable = {0}SubmitCtrl.sh\n".format(
            handler.resourcedir))
        file.write("Error = {0}log.$(ID).err\n".format(logPath))
        file.write("Output = {0}log.$(ID).out\n".format(logPath))
        file.write("Log = /scratch/rturcotte/log.$(ID).log\n")

        if UseParallel:
            file.write("Universe = parallel\n")
            file.write("machine_count = 4\n")
            file.write("request_memory = 8GB\n")
        else:
            file.write("Universe = vanilla\n")
            file.write("request_memory = 2GB\n")
            file.write("+AccountingGroup=\"1_week.$ENV(USER)\" \n\n\n")

        file.write("Arguments= --id $(ID) ")

    if UseStar:
        file.write("--usestar ")

    file.write("--zenith {0} ".format(zen))
    file.write("--energy {0} ".format(eng))
    file.write("--primary {0} ".format(prim))
    file.write("--azimuth {0} ".format(azi))

    file.write("--runID {0} ".format(runID))
    file.write("--eventID {0} ".format(eventID))

    if UseParallel:
        file.write("--parallel ")

    file.write("--temp ")
    # file.write("--nothin ")
    # file.write("--fixedcore ")

    if DoThin(eng, zen):
        file.write("--thin ")

    if SendToCondor:
        file.write("--movetocondor ")

    if UseRealAtmos:
        file.write("--realAtmosphere ")

    file.write("\n")

    if "icecube" == cluster:
        file.write("Queue {0}\n".format(n))

    file.close()


# Some sanity checks and logs...
def writeLog(runId, eventId, zenith, azimuth, energy, primaries, nShowers):
    from datetime import date
    filename = "/data/user/rturcotte/corsika_simulation/log/simulated_showers.txt"
    log = open(filename, "a")
    log.write("=============================================== \n")
    log.write("star : {0}".format(UseStar))
    log.write("{0} \n".format(date.today()))
    log.write("runId {0}, eventId {1} \n".format(runId, eventId))
    log.write("Zenith  : {0}  in deg\n".format(zenith))
    log.write("CoREAS Azi : {0} in deg\n".format(azimuth))
    log.write("Energy  : {0} in PeV\n".format(energy))
    log.write("Primaries : {0}  \n".format(primaries))
    log.write("nShowers: {0}  \n".format(nShowers))
    log.write("=============================================== \n")
    log.close()
    print("Writing a log file in ... {0}".format(filename))


def plotSimulatedShowersProperties(showerFile, wantedEvents, plotname="events.png"):
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    runIds, eventIds, zens, azis, energies = pickEvents(showerFile, wantedEvents)
    fig = plt.figure(figsize=[8, 10])
    gs = gridspec.GridSpec(2, 1, wspace=0.3, hspace=0.2)

    # one day, invert the zenith axis
    ax = fig.add_subplot(gs[0], polar=True)
    ax.scatter(azis, zens, c="indigo")
    ax.set_xlabel("azimuth")
    ax.set_ylabel("zenith")

    ax = fig.add_subplot(gs[1], polar=False)
    ax.scatter(np.arange(0, len(energies)), energies, c="indigo")
    ax.set_xlabel("shower")
    ax.set_ylabel("energy [PeV]")
    print("Plotting the variables of the showers...")
    plt.savefig("/data/user/rturcotte/corsika_simulation/plot/" + plotname)


def pickEvents(showerFile, wantedEvents):
    runIds, eventIds, zens, azis, energies = [], [], [], [], []
    in_file = dataio.I3File(showerFile, 'r')
    for frame in in_file:
        runId, eventId = i3var.getRunIdEventIdfromI3File(frame)
        if in_file.stream == I3Frame.DAQ:
            if [runId, eventId] in wantedEvents:
                print("Got it! : {0}, {1}".format(runId, eventId))
                runIds.append(runId)
                eventIds.append(eventId)
                zens.append(i3var.getIceTopZenith(frame) / I3Units.degree)
                azis.append(aziI3ParticleToCoREAS(i3var.getIceTopAzimuth(frame)) / I3Units.degree)
                energies.append(i3var.getIceTopEnergy(frame) / I3Units.PeV)
    return runIds, eventIds, zens, azis, energies


def aziI3ParticleToCoREAS(azimuth):
    return azimuth - radcube.GetMagneticRotation()


showerList = []

if (__name__ == '__main__'):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "showerEnergy", "/home/rturcotte/work/scripts/showerEnergy/utils/extractI3Variables.py")
    i3var = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(i3var)

    proton = 14
    iron = 5626
    nShowers = 10

    # showerFile = "/data/user/rturcotte/showers/showersV4_12112020.i3.gz"
    #showerFile = "/data/user/rturcotte/showers/showersV4_coinc_20210217.i3.gz"
    showerFile = "/data/user/rturcotte/showers/showersV4_20210217_clear.i3.gz"
    clearEvents = [[134244,  71221068],
                     [134247,  69331046],
                     [134287,  65746633],
                     [134304,  28903706],
                     [134335,  22026909],
                     [134401,  26153108],
                     [134402,  27870115]]
    events = np.array(pd.read_csv('/data/user/rturcotte/showers/clearEvents.txt', header=None, comment="#", sep=" "))

    runIds, eventIds, zens, azis, energies = pickEvents(showerFile, events)
    for i in range(len(runIds)):
        print(runIds[i], eventIds[i], zens[i], azis[i], energies[i])
        writeLog(runIds[i], eventIds[i], zens[i], azis[i], energies[i], [proton, iron], nShowers)
        # showerList += ShowerString(runID, eventID, Zenith Angle deg, Azimuth Angle deg, Energie PeV, [Primaries],
    showerList += ShowerString(runIds[0], eventIds[0], zens[0], azis[0], 1, [proton, iron], 1)
    for shwr in showerList:
        shwr.SubmitShowers()
    # plotSimulatedShowersProperties(showerFile, coincEvents, plotname="coincEvent.png")
