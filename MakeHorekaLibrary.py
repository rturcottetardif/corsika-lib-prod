#!/usr/bin/env python3

import os
import subprocess
import pathlib
import numpy as np
from python_tools import FileHandler
import time

#### YOU CANT USE STAR AND PROTOTYPE ! is both false, uses complete array
UseCONEX = False
UseStar = True
UsePrototype = False
UseRealAtmos = True


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

    def __init__(self, filename, runID, eventID, prim, n):
        self.runID = runID
        self.eventID = eventID
        self.filename = filename
        self.zenith = 0
        self.azimuth = 0
        self.energy = 0  # [PeV]
        self.coreX = 0
        self.coreY = 0
        self.primary = prim
        self.nShowers = n

        self.seed = False
        self.fixHeight = False

        self.getShowerInfo()

    def getShowerInfo(self):
        event = np.array((0, 0), dtype=([('runId', np.int), ('eventId', np.int)]))
        with open(self.filename, 'rb') as f:
            while not (event['runId'] == self.runID and event['eventId'] == self.eventID):
                try:
                    event = np.load(f)
                except ValueError:
                    print("The runId {0}, eventId {1} was not found !".format(self.runID, self.eventID))
                    exit()

        self.zenith = event["zenith"]       # [Deg]
        self.azimuth = event["azimuth"]     # [Deg]
        self.energy = event["energy"]       # [PeV]
        self.coreX = event["coreX_Ant"]     # [cm]
        self.coreY = event["coreY_Ant"]     # [cm]

    ##Allows the manual modification of parameters
    def setEnergy(self, energy):
        self.energy = energy

    def setCore(self, core):
        self.coreX = core[0]
        self.coreY = core[1]

    def setZenith(self, zen):
        self.zenith = zen

    def setAzimuth(self, azi):
        self.azimuth = azi

    def setSeed(self, seed):
        self.seed = seed

    def setFixHeight(self, height):
        self.fixHeight = height

    def printShowerInfo(self):
        print("{0} \n runID {1}, eventID {2}, zen {3}, azi {4}, ener {5}, core {6} {7}, prim {8}, n {9} ".format(
              self.filename,
              self.runID, self.eventID,
              self.zenith, self.azimuth,
              self.energy,
              self.coreX, self.coreY,
              self.primary, self.nShowers))

    def SubmitShowers(self, IdBegin=0):

        MakeSubFile(self.runID, self.eventID,
                    self.zenith, self.azimuth,
                    self.energy, self.coreX,
                    self.coreY, self.primary,
                    self.nShowers, IdBegin,
                    fixHeight=self.fixHeight,
                    seed=self.seed)

        cluster = GetCluster()
        if "caviness" == cluster:
            group = os.environ['WORKGROUP']
            print("Submitting on workgroup", group)

            subprocess.call(["sbatch", "--partition=" +
                             str(group), "tempSubFile.submit"])

        elif "horeka" == cluster:
            submit = True
            while submit:
                results = subprocess.call(["sbatch", "--partition=cpuonly", "-A", "hk-project-pevradio", "tempSubFile.submit"])
                if results:
                    print("... I'm waiting 5 minutes before trying again")
                    time.sleep(5*60)
                    submit = True
                else:
                    submit = False

        elif "asterix" == cluster:
            subprocess.call(["sbatch", "tempSubFile.submit"])

        elif "icecube" == cluster:
            subprocess.call(["condor_submit", "tempSubFile.submit", "-batch-name",
                             "{0:0.0f}_{1:0.1f}".format(self.zenith, np.log10(self.energy) + 15)])

        # subprocess.call(["rm", "tempSubFile.submit"])


def ShowerString(filename, runID, eventID, prims, n, **kwargs):
    tempList = []
    for prim in prims:
        shwr = ShowerGroup(filename, runID, eventID, prim, n)
        if 'zenith' in kwargs.keys():
            print("Changing zenith from {0} to {1}".format(shwr.zenith, kwargs['zenith']))
            shwr.setZenith(kwargs['zenith'])
        if 'azimuth' in kwargs.keys():
            print("Changing azimuth from {0} to {1}".format(shwr.azimuth, kwargs['azimuth']))
            shwr.setAzimuth(kwargs['azimuth'])
        if 'core' in kwargs.keys():
            print("Changing core from [{0}, {1}] to {2}".format(shwr.coreX, shwr.coreY, kwargs['core']))
            shwr.setCore(kwargs['core'])
        if 'energy' in kwargs.keys():
            print("Changing energy from {0} to {1}".format(shwr.energy, kwargs['energy']))
            shwr.setEnergy(kwargs['energy'])
        if 'fixHeight' in kwargs.keys():
            shwr.setFixHeight(kwargs['fixHeight'])
            print("fixing the first interaction at {0}".format(shwr.fixHeight))
        tempList.append(shwr)
    return tempList


def DoThin(peV, zenith):
    return True


def MakeSubFile(runID, eventID, zen, azi, eng, coreX, coreY, prim, n, id, **kwargs):

    print("Making subfile begining with id", id)
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
            # Uncommment this line to longer processing time
            # if UseStar and not UseCONEX:
            # file.write("+AccountingGroup=\"1_week.$ENV(USER)\" \n\n\n")

        file.write("Arguments= --id $(ID) ")

    if UseStar:
        file.write("--usestar ")
    if UsePrototype:
        file.write("--proto ")

    file.write("--zenith {0} ".format(zen))
    file.write("--energy {0} ".format(eng))
    file.write("--primary {0} ".format(prim))
    file.write("--azimuth {0} ".format(azi))
    file.write("--coreX {0} ".format(coreX))
    file.write("--coreY {0} ".format(coreY))

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

    if UseCONEX:
        file.write("--fastShowers ")

    if kwargs["fixHeight"]:
        file.write("--fixHeight "+str(kwargs["fixHeight"])+" ")
    if kwargs['seed']:
        file.write("--seed "+str(kwargs["seed"])+" ")
    file.write("\n")

    if "icecube" == cluster:
        file.write("Queue {0}\n".format(n))

    file.close()


# # Some sanity checks and logs...
# def writeLog(runId, eventId, zenith, azimuth, energy, primaries, nShowers):
#     from datetime import date
#     filename = handler.logfiledir + "/simulated_showers.txt"
#     log = open(filename, "a")
#     log.write("=============================================== \n")
#     log.write("star : {0}, fast : {1} \n".format(UseStar, useCONEX))
#     log.write("{0} \n".format(date.today()))
#     log.write("runId {0}, eventId {1} \n".format(runId, eventId))
#     log.write("Zenith  : {0}  in deg\n".format(zenith))
#     log.write("CoREAS Azi : {0} in deg\n".format(azimuth))
#     log.write("Energy  : {0} in PeV\n".format(energy))
#     log.write("Primaries : {0}  \n".format(primaries))
#     log.write("nShowers: {0}  \n".format(nShowers))
#     log.write("=============================================== \n")
#     log.close()
#     print("Writing a log file in ... {0}".format(filename))


# def plotSimulatedShowersProperties(showerFile, wantedEvents, plotname="events.png"):
#     import matplotlib.pyplot as plt
#     import matplotlib.gridspec as gridspec
#     runIds, eventIds, zens, azis, energies = pickEvents(showerFile, wantedEvents)
#     fig = plt.figure(figsize=[8, 10])
#     gs = gridspec.GridSpec(2, 1, wspace=0.3, hspace=0.2)

#     # one day, invert the zenith axis
#     ax = fig.add_subplot(gs[0], polar=True)
#     ax.scatter(azis, zens, c="indigo")
#     ax.set_xlabel("azimuth")
#     ax.set_ylabel("zenith")

#     ax = fig.add_subplot(gs[1], polar=False)
#     ax.scatter(np.arange(0, len(energies)), energies, c="indigo")
#     ax.set_xlabel("shower")
#     ax.set_ylabel("energy [PeV]")
#     print("Plotting the variables of the showers...")
#     plt.savefig(handler.logfiledir + plotname)


# showerList = []
def printSettings():
    print("I will use the star pattern ...", UseStar)
    print("I will use the prototype station layout ...", UsePrototype)
    print("I will use the real atmosphere...", UseRealAtmos)
    print("I will use the CONEX option...", UseCONEX)
    print("I start the simulation at ", IdBegin)
    print("I simulate {0} showers of proton and {0} of iron".format(nShowers))


def simulateOneFile(filename, IdBegin=0):
    printSettings()
    showerList = []
    with open(filename, 'rb') as f:
        next = True
        while next:
            try:
                event = np.load(f)
                """showerList += ShowerString(file_with_showers, runID, eventID, [Primaries], nSimulations)"""
                showerList += ShowerString(filename, event["runId"], event["eventId"], [proton, iron], nShowers)
            except ValueError:
                for i, shwr in enumerate(showerList):
                    shwr.SubmitShowers(IdBegin)
                    if Increment:
                        IdBegin += nShowers
                next = False
                exit()


if (__name__ == '__main__'):
    proton = 14
    iron = 5626

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, default=handler.basedir + "/resources/exampleShowerlist.npy",
                        help='List of CoREAS simulation directories')
    parser.add_argument('-n', '--nShowers', type=int, default=20,
                        help='number of simulation of proton and iron')
    parser.add_argument('--no-conex', dest='conex', action='store_false',
                        help='The simulation will use the standard coreas')
    parser.add_argument('--conex', dest='conex', action='store_true',
                        help='The simulation will use conex')
    parser.add_argument('--no-atmos', dest='noAtmos', action='store_false',
                        help='The simulation will use the standard aatmosphere')
    parser.add_argument('--atmos', dest='atmos', action='store_true',
                        help='The simulation will use the standard aatmosphere')
    parser.add_argument('--id', type=int, default=0,
                        help='The starting number of the simulations')
    parser.add_argument('-p', '--prototype', dest='proto', action='store_true',
                        help='Will simulate on protytpe station layout')
    parser.add_argument('-i', '--increment', dest='increment', action='store_true',
                        help='This is to be used if the same runID is multiple time in the file')
    parser.add_argument('--test', dest='test', action='store_true',
                        help='just for testing')
    parser.set_defaults(conex=False)
    parser.set_defaults(atmos=True)
    parser.set_defaults(proto=False)
    parser.set_defaults(test=False)
    parser.set_defaults(increment=False)
    args = parser.parse_args()

    # --------------------
    # Setting the simulation properties
    IdBegin = args.id
    Increment = args.increment
    nShowers = args.nShowers
    UseCONEX = args.conex
    UseStar = not args.proto
    UsePrototype = args.proto
    UseRealAtmos = args.noAtmos
    proton = 14
    iron = 5626

    # ======================
    ## EXAMPLE : SIMULATING ONE EVENT
    if args.test:
    # if you use the test option be careful to remove that simulation afterwards
        runId = 134774
        eventId = 7861658
        # runId = 134777
        # eventId = 12754797
        nShowers = 1
        print("ID: ", IdBegin)

        showerList = []
        """showerList += ShowerString(file_with_showers, runID, eventID, [Primaries], nSimulations)"""
        showerList += ShowerString(args.input, runId, eventId, [proton, iron], nShowers)
        for i, shwr in enumerate(showerList):
            # shwr.setEnergy(10)
            shwr.SubmitShowers(IdBegin)
    # ======================

    else:
        simulateOneFile(args.input, IdBegin)
        #printSettings()


    # VARYING THE ENERGY
    # with open(filename, 'rb') as f:
    #     event = np.array((0, 0), dtype=([('runId', np.int), ('eventId', np.int)]))
    #     while not (event['runId'] == runId and event['eventId'] == eventId):
    #         try:
    #             event = np.load(f)
    #         except ValueError:
    #             print("The runId {0}, eventId {1} was not found !".format(runId, eventId))
    #             exit()
    #     energy = event['energy']

    # energy_array = np.linspace(energy/2, 2*energy, 10)





