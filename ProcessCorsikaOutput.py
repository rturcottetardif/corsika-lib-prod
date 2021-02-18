#!/bin/env python3

#This script runs a reconstruction of the CORSIKA simulations for Scint+Ant
#Currently this only works in the discrete library
#Supply the zenith angles and the energies that you want to simulate


import numpy as np

import glob
import os
import subprocess
from util import variables
import pathlib

#####################################################

ram = 8
nQueue = 400
prims = ["proton"]

zens = [0, 17, 34, 51, 68]
zens = [17]

engs = np.arange(16.0, 17.0, 0.1)
engs = np.arange(16.5, 16.9, 0.1)
engs = [16.0, 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8, 16.9]
engs = [16.5, 16.6, 16.7]

baseDir = "/data/sim/IceCubeUpgrade/CosmicRay/Radio/coreas/data/discrete"

#####################################################


def MakeAndSubmit(directory):

  MakeSubFile(directory)

  cluster = GetCluster()
  if "caviness" == cluster:
    group = os.environ['WORKGROUP']
    print("Submitting on workgroup", group)

    subprocess.call(["sbatch", "--partition="+str(group), "tempSubFile.submit"])

  elif "asterix" == cluster:
    subprocess.call(["sbatch", "tempSubFile.submit"])

  elif "icecube" == cluster:
    pieces = directory.split("/")[-3:]
    subprocess.call(["condor_submit", "tempSubFile.submit", "-batch-name", "{0}_{1}_{2}".format(pieces[0], pieces[1], pieces[2])])

  subprocess.call(["rm", "tempSubFile.submit"])



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



vars = variables.Variables()



def MakeSubFile(directory):

  print("Making subfile for ", directory.replace("/*/DAT??????", ""))

  file = open("tempSubFile.submit", "w")

  file.write("#!/bin/bash\n")

  chunks = directory.split("/")[-2:]
  logPath = str(vars.logfiledir) + "/discrete/"
  pathlib.Path(logPath).mkdir(parents=True, exist_ok=True)

  eng = chunks[0]
  zen = chunks[1]

  cluster = GetCluster()
  if "caviness" == cluster or "asterix" == cluster:

    file.write("#SBATCH --job-name={0}_{1}\n".format(chunks[0],chunks[1]))
    file.write("#SBATCH --output={0}log.%a.out\n".format(logPath))
    file.write("#SBATCH --nodes=1\n")

    if "caviness" == cluster:
      file.write("#SBATCH --export=NONE\n")

    file.write("#SBATCH --time=7-00:00:00\n")
    file.write("#SBATCH --tasks-per-node=1\n")
    file.write("#SBATCH --mem-per-cpu={}\n".format(int(ram * 1024)))
    if "asterix" == cluster:
      file.write("#SBATCH --partition=long\n")

    file.write("{0}ProcessCtrl.sh ".format(vars.resourcedir))
    file.write(str(directory))

  elif "icecube" == cluster:
    file.write("Executable = {0}ProcessCtrl.sh\n".format(vars.resourcedir))
    file.write("Error = {0}i3.{1}_{2}_$(Process).out\n".format(logPath, eng, zen))
    file.write("Output = {0}i3.{1}_{2}_$(Process).out\n".format(logPath, eng, zen))
    file.write("Log = /scratch/acoleman/i3.{0}_{1}_$(Process).log\n".format(eng, zen))
    file.write("Universe = vanilla\n")
    file.write("request_memory = {}GB\n".format(ram))
    #file.write("+AccountingGroup=\"1_week.$ENV(USER)\" \n\n\n")

    file.write("Arguments= {} $(Process)".format(directory))

  file.write("\n")

  if "icecube" == cluster:
    file.write("Queue {}\n".format(nQueue))    

  file.close()


showerList = []

if (__name__ == '__main__'):

  for prim in prims:
    primDir = baseDir+"/"+prim
    if not os.path.isdir(primDir):
      print("WARNING:", primDir, "does not exist!")
      continue

    for eng in engs:
      engDir = primDir+"/lgE_{0:0.1f}".format(eng)
      if not os.path.isdir(engDir):
        print("WARNING:", engDir, "does not exist!")
        continue

      for zen in zens:
        zenDir = engDir+"/Zen_{0}".format(zen)
        if not os.path.isdir(zenDir):
          print("WARNING:", zenDir, "does not exist!")
          continue

        MakeAndSubmit(zenDir)
