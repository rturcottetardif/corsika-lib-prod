#!/usr/bin/env python3

import os
import subprocess
from python_tools import FileHandler
import pathlib

IdBegin = 0
UseStar = True
SendToCondor = True

handler = FileHandler.FileHandler()

IdCurrent = IdBegin

def GetCluster():

  stdout,stderr = subprocess.Popen(['hostname', '-d'], 
             stdout=subprocess.PIPE, 
             stderr=subprocess.STDOUT).communicate()

  if "icecube" in str(stdout):
    return "icecube"

  stdout,stderr = subprocess.Popen(['hostname', '-s'], 
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
  def __init__(self, zen, eng, prim, n):
    self.zenith = zen
    self.energy = eng #[PeV]
    self.primary = prim
    self.nShowers = n

  def SubmitShowers(self):
    global IdCurrent

    MakeSubFile(self.zenith, self.energy, self.primary, self.nShowers, IdCurrent)
    #IdCurrent += self.nShowers


    cluster = GetCluster()
    if "caviness" == cluster:
      group = os.environ['WORKGROUP']
      print("Submitting on workgroup", group)

      subprocess.call(["sbatch", "--partition="+str(group), "tempSubFile.submit"])

    elif "asterix" == cluster:
      print("You are on Asterix")
      subprocess.call(["sbatch", "tempSubFile.submit"])

    elif "icecube" == cluster:
      print("You are on NPX")
      subprocess.call(["condor_submit", "tempSubFile.submit", "-batch-name", "{0:0.1f}_{1:0.2f}".format(self.zenith[0], self.energy)])

    # subprocess.call(["rm", "tempSubFile.submit"])

def ShowerString(zens, engs, prim, n):
  tempList = []
  for zen in zens:
    for eng in engs:
      shwr = ShowerGroup(zen, eng, prim, n)
      tempList.append(shwr)

  return tempList


def DoThin(lgE, sin2):
  return True


def MakeSubFile(zen, eng, prim, n, id):

  print("Making subfile begining with id", IdBegin)

  file = open("tempSubFile.submit", "w")

  file.write("#!/bin/bash\n")
  logPath = str(handler.logfiledir) + "/continuous/Zen{0:0.1f}/Eng{1:0.1f}/".format(zen[0],eng)
  pathlib.Path(logPath).mkdir(parents=True, exist_ok=True)

  cluster = GetCluster()
  if "caviness" == cluster or "asterix" == cluster:

    file.write("#SBATCH --job-name={0:0.1f}_{1:0.2f}\n".format(zen[0], eng))
    file.write("#SBATCH --output={0}log.%a.out\n".format(logPath))
    file.write("#SBATCH --nodes=1\n")

    if "caviness" == cluster:
      file.write("#SBATCH --export=NONE\n")

    file.write("#SBATCH --time=7-00:00:00\n")
    file.write("#SBATCH --tasks-per-node=1\n")
    file.write("#SBATCH --mem-per-cpu=4096\n")
    if "asterix" == cluster:
      file.write("#SBATCH --partition=long\n")

    file.write("#SBATCH --array=0-{0}\n".format(int(n-1)))
    file.write("\nSTARTID={0}\n".format(id))
    file.write("ARRAYID=$SLURM_ARRAY_TASK_ID\n")
    file.write("ID=$(($STARTID + $ARRAYID))\n\n")

    file.write("{0}SubmitCtrl.sh ".format(handler.resourcedir))
    file.write("--id $ID ")

  elif "icecube" == cluster:
    file.write("StartIDOffset={0}\n".format(id))
    file.write("ID=$$([$(Process) + $(StartIDOffset)])\n\n\n")

    file.write("Executable = {0}SubmitCtrl.sh\n".format(handler.resourcedir))
    file.write("Error = {0}log.$(ID).err\n".format(logPath))
    file.write("Output = {0}log.$(ID).out\n".format(logPath))
    file.write("Log = /scratch/acoleman/log.$(ID).log\n")
    
    file.write("Universe = vanilla\n")
    file.write("request_memory = 4GB\n")
    #file.write("+AccountingGroup=\"1_week.$ENV(USER)\" \n\n\n")

    file.write("Arguments= --id $(ID) ")

  if UseStar:
    file.write("--usestar ")

  file.write("--minSin2 {0} ".format(zen[0]))
  file.write("--maxSin2 {0} ".format(zen[1]))
  file.write("--randazi ")

  file.write("--minLgE {0} ".format(eng))
  file.write("--energyIndex {0} ".format(-1))

  file.write("--primary {0} ".format(prim))

  file.write("--temp ")

  if DoThin(eng, zen[1]):
    file.write("--thin ")

  if SendToCondor:
    file.write("--movetocondor ")

  file.write("\n")

  if "icecube" == cluster:
    file.write("Queue {0}\n".format(n))    

  file.close()


showerList = []

if (__name__ == '__main__'):

  proton = 14
  iron = 5626

  #showerList += ShowerString([sin2low, sin2high],[Energies], Primary, NShowers)
  showerList += ShowerString([[0.7, 0.8]], [17.6, 17.7, 17.8], iron, 200)

  for shwr in showerList:
    shwr.SubmitShowers()
