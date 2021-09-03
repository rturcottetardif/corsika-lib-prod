#!/usr/bin/env python3

import os
import subprocess
import pathlib
import numpy as np
from python_tools import FileHandler

IdBegin = 0

UseStar = True
# Always use real atmosphere for measured shower ! otherwise it will break the folders
UseRealAtmos = True
#FastShowers = True

SendToCondor = False
UseParallel = False

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

    if "hkn" in str(stdout):
        return "horeka"
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

        elif "horeka" == cluster:
            subprocess.call(["sbatch", "--partition=cpuonly", "-A", "hk-project-pevradio", "tempSubFile.submit"])

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
    if "caviness" == cluster or "asterix" == cluster or "horeka" == cluster:

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

        elif "horeka" == cluster:
            file.write("#SBATCH --constraint=LSDF\n")
            if UseParallel:
                # DOESN'T WORK YET... To be fix
                #  CoREAS: Error reading parameter file anynameupto239characters/SIM000000.reas!
                file.write("#SBATCH --time=12:00:00\n")
                file.write("#SBATCH --tasks-per-node=6\n")
                #file.write("#SBATCH --mem-per-cpu=2000\n")
            else:
                file.write("#SBATCH --time=3-00:00:00\n")
                file.write("#SBATCH --tasks-per-node=1\n")
                #file.write("#SBATCH --mem-per-cpu=1600\n")

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
            if UseStar and not FastShowers:
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

    if FastShowers:
        file.write("--fastShowers")
    file.write("\n")

    if "icecube" == cluster:
        file.write("Queue {0}\n".format(n))

    file.close()


# Some sanity checks and logs...
def writeLog(runId, eventId, zenith, azimuth, energy, primaries, nShowers):
    from datetime import date
    filename = handler.logfiledir + "/simulated_showers.txt"
    log = open(filename, "a")
    log.write("=============================================== \n")
    log.write("star : {0}, fast : {1} \n".format(UseStar, FastShowers))
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
    plt.savefig(handler.logfiledir + plotname)


def simulateWholeFile(filename, nShowers):
    showerList = []
    with open(filename, 'rb') as f:
        try:
            while 1:
                event = np.load(f)
                print("runId {0} eventId {1} zen {2} azi {3} energy {4}".format(event["runId"], event["eventId"], event["zenith"], event["azimuth"]-60, event["energy"]))
                writeLog(event["runId"], event["eventId"], event["zenith"], event["azimuth"], event["energy"], [proton, iron], nShowers)
                showerList += ShowerString(event["runId"], event["eventId"], event["zenith"], event["azimuth"], event["energy"], [proton, iron], nShowers)
        except ValueError: #Sketchy fix
            print("EoF : ", filename)
        return showerList


def simulateOneEvent(filename, nShowers, runId, eventId):
    showerList = []
    with open(filename, 'rb') as f:
        try:
            while 1:
                event = np.load(f)
                if (str(event["runId"]) == runId) and (str(event["eventId"]) == eventId):
                    print("runId {0} eventId {1} zen {2} azi {3} energy {4}".format(event["runId"], event["eventId"], event["zenith"], event["azimuth"]-60, event["energy"]))
                    writeLog(event["runId"], event["eventId"], event["zenith"], event["azimuth"], event["energy"], [proton, iron], nShowers)
                    showerList += ShowerString(event["runId"], event["eventId"], event["zenith"], event["azimuth"], event["energy"], [proton, iron], nShowers)
        except ValueError: #Sketchy fix
            print("EoF : ", filename)
        return showerList


showerList = []

if (__name__ == '__main__'):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, default=handler.basedir + "/resources/exampleShowerlist.npy",
                        help='List of CoREAS simulation directories')
    parser.add_argument('--batch', type=int, default=1, help='batch number')
    parser.add_argument('--nshowers', type=int, default=50, help='number of simulation of each type')
    parser.add_argument('--conex', type=bool, default=True, help='fast simulations')
    parser.add_argument('--test', type=bool, default=False, help='just for testing')
    args = parser.parse_args()

    FastShowers = args.conex
    proton = 14
    iron = 5626
    nShowers = 50

    if not args.test:
        # RUN ALL SHOWERS IN THE FILE
        showerList = simulateWholeFile(args.input, nShowers)
        ## BATCHES of 6
        batch = args.batch # starts at 1
        for i, shwr in enumerate(showerList):
            shwr.SubmitShowers()


    # =======================
    ## TEST RUN - FIX ATMOS FOR REAL SHOWERS!
    if args.test:
        runIds = 134625
        eventIds = 31078935
        zens = 30
        azis = 180
        energies = 0.180
        nShowers = 1
        """showerList += ShowerString(runID, eventID, Zenith Angle deg, Azimuth Angle deg, Energie PeV, [Primaries])"""
        showerList += ShowerString(runIds, eventIds, zens, azis, energies, [proton, iron], nShowers)
        print("runId {0} eventId {1} zen {2} azi {3} energy {4}".format(runIds, eventIds, zens, azis-60, energies))

        for shwr in enumerate(showerList):
                shwr.SubmitShowers()


