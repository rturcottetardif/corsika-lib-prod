#!/usr/bin/env python3

import os
import subprocess
import pathlib
import numpy as np
from python_tools import FileHandler

IdBegin = 0
UseParallel = False
UseStar = False
SendToCondor = True

handler = FileHandler.FileHandler()

def GetCluster():

  stdout,stderr = subprocess.Popen(['hostname', '-d'], 
             stdout=subprocess.PIPE, 
             stderr=subprocess.STDOUT).communicate()

  if "icecube" in str(stdout):
    return "icecube"

  if "Darwin" == os.getenv("CLUSTERNAME"):
    return "darwin"

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
  def __init__(self, zen, eng, azi, prim, n):
    self.zenith = zen
    self.energy = eng #[PeV]
    self.azimuth = azi
    self.primary = prim
    self.nShowers = n

  def SubmitShowers(self):

    MakeSubFile(self.zenith, self.energy, self.azimuth, self.primary, self.nShowers, IdBegin)

    cluster = GetCluster()
    if "caviness" == cluster:
      group = os.environ['WORKGROUP']
      print("Submitting on workgroup", group)

      subprocess.call(["sbatch", "--partition="+str(group), "tempSubFile.submit"])

    elif "darwin" == cluster:
      subprocess.call(["sbatch", "tempSubFile.submit"])

    elif "asterix" == cluster:
      subprocess.call(["sbatch", "tempSubFile.submit"])

    elif "icecube" == cluster:
      subprocess.call(["condor_submit", "tempSubFile.submit", "-batch-name", "{0:0.0f}_{1:0.1f}".format(self.zenith, np.log10(self.energy)+15)])

    subprocess.call(["rm", "tempSubFile.submit"])

def ShowerString(zens, engs, azi, prim, n):
  tempList = []
  for zen in zens:
    for eng in engs:
      shwr = ShowerGroup(zen, eng, azi, prim, n)
      tempList.append(shwr)

  return tempList

def DoThin(peV, zenith):
  return True  #In the current scheme, we always use thinning, left here in case this changes

def MakeSubFile(zen, eng, azi, prim, n, id):

  print("Making subfile begining with id", IdBegin)
  print("Zen {}, Eng {}, azi {}".format(zen, eng, azi))

  file = open("tempSubFile.submit", "w")

  file.write("#!/bin/bash\n")

  logPath = str(handler.logfiledir) + "/discrete/Zen{0:0.1f}/Eng{1:0.1f}/".format(zen,eng)
  pathlib.Path(logPath).mkdir(parents=True, exist_ok=True)

  cluster = GetCluster()
  if cluster in ["darwin", "caviness", "asterix"]:

    file.write("#SBATCH --job-name={0:0.0f}_{1:0.1f}\n".format(zen, np.log10(eng)+15))
    file.write("#SBATCH --output={0}log.%a.out\n".format(logPath))
    file.write("#SBATCH --nodes=1\n")

    if cluster in ["caviness", "darwin"]:
      file.write("#SBATCH --export=NONE\n")

    if UseParallel:
      file.write("#SBATCH --time=12:00:00\n")
      file.write("#SBATCH --tasks-per-node=6\n")
      file.write("#SBATCH --mem-per-cpu=2000\n")
    else:
      file.write("#SBATCH --time=3-12:00:00\n")
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
    
    if UseParallel:
      file.write("Universe = parallel\n")
      file.write("machine_count = 4\n")
      file.write("request_memory = 8GB\n")
    else:
      file.write("Universe = vanilla\n")
      file.write("request_memory = 2GB\n")
      #file.write("+AccountingGroup=\"1_week.$ENV(USER)\" \n\n\n")

    file.write("Arguments= --id $(ID) ")

  if UseStar:
    file.write("--usestar ")

  file.write("--zenith {0} ".format(zen))
  file.write("--energy {0} ".format(eng))
  file.write("--primary {0} ".format(prim))
  file.write("--azimuth {0} ".format(azi))
  
  if UseParallel:
    file.write("--parallel ")

  file.write("--temp ")

  if DoThin(eng, zen):
    file.write("--thin ")

  if SendToCondor:
    file.write("--movetocondor ")

  file.write("\n")

  if "icecube" == cluster:
    file.write("Queue {0}\n".format(n))    

  file.close()


showerList = []

if (__name__ == '__main__'):

  aligned = 180 #deg
  anti = 0 #deg
  proton = 14
  iron = 5626

  #showerList += ShowerString([Zenith Angles deg],[Energies PeV], Azimuth deg, Primary, NShowers)

  #showerList += ShowerString([0],[0.001], anti, proton, 1)

  showerList += ShowerString([20],[10**-3], anti, proton, 1)
  
  for shwr in showerList:
    shwr.SubmitShowers()




