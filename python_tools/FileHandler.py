#!/usr/bin/python3

import os
from pathlib import Path
from . import CorsikaOptions
import numpy as np


class FileHandler(object):
  """docstring for FileHandler"""
  def __init__(self):
    self.basedir =  "NOTSET" ##location of basefiles
    self.datadir = "NOTSET" ##location of processed data
    self.logfiledir = "NOTSET"  ##location to put grid-log files in (.out/.err)
    self.tempdir = "NOTSET"  ##location to make showers before copying them to final location (if using --temp flag)
    self.atmosdir = "NOTSET"  #location of the real atmosphere directory
    self.i3dir = "NOTSET" #location of the i3file from simulations

    self.corsikadir = "NOTSET"
    self.corsikaexe = "NOTSET"
    self.corsikanothin = "NOTSET"
    self.corsikampi = "NOTSET"

    self.runID = "NOTSET"
    self.eventID = "NOTSET"

    self.corOpts = CorsikaOptions.CorsikaOptions()
    self.InitDirectories()

    self.useTempDir = False

  def AssertFinalSlash(self, filename):
    if not filename[-1] == '/':
      filename +='/'
    return filename

  def InitDirectories(self):
    ###################################
    ##  Read in the directory locations
    ###################################

    here = os.path.abspath(__file__)
    here = os.path.split(here)[0]

    self.basedir = str(Path(here).parent)
    self.resourcedir = os.path.join(self.basedir, "resources/")

    toLoad = os.path.join(self.basedir, "resources/DataLocations.txt")
    if not os.path.isfile(toLoad):
      print("WARNING::variables.py  something went wrong. Could not find", toLoad)
      exit()

    ### Check that the directories loaded up correctly.
    file = open(toLoad, "r")
    for line in file:

      if str(line)[0] == "#":
        continue

      columns = line.split()
      if len(columns) < 2:
        continue

      flag = columns[0]


      if flag == "CORSIKA_DIR":
        self.corsikadir = self.AssertFinalSlash(columns[2])
      elif flag == "CORSIKA_EXE":
        self.corsikaexe = columns[2]
      elif flag == "CORSIKA_MPI":
        self.corsikampi = columns[2]
      elif flag == "CORSIKA_NOTHIN":
        self.corsikanothin = columns[2]
      elif flag == "DATA_DIR":
        self.datadir = self.AssertFinalSlash(columns[2])
      elif flag == "LOGFILE_DIR":
        self.logfiledir = self.AssertFinalSlash(columns[2])
      elif flag == "TEMP_DIR":
        self.tempdir = self.AssertFinalSlash(columns[2])
      elif flag == "I3FILE_DIR":
        self.i3dir = self.AssertFinalSlash(columns[2])
      elif flag == "ATMOS_DIR":
        self.atmosdir = self.AssertFinalSlash(columns[2])

  def GetResourceDir(self):
    return self.basedir + "/resources"

  def CheckDataLocationExists(self, string, isfile = False):
    if not isfile and not os.path.exists(string):
      print("The directory", string, "does not exists. Update", self.GetResourceDir() + "/DataLocations.txt")
      exit()
    elif not os.path.exists(string):
      print("The file", string, "does not exists. Update", self.GetResourceDir() + "/DataLocations.txt")

  def SixDigitID(self):
    return "{0:06d}".format(self.corOpts.eventID)

  def GetLibraryDirectory(self):
    subDir = ""

    libType = self.corOpts.GetLibraryType()

    if 0 == libType:
      subDir += "continuous/"
      if self.corOpts.useStar:
        subDir += "star-pattern/"
      else:
        subDir += "array-2020/"
    if 1 == libType:
      subDir += "realEvents/"
      if self.corOpts.useStar:
        subDir += "star-pattern/"
      else:
        subDir += "array-2020/"

    # subDir += self.corOpts.GetPrimaryName() + "/"

    if 0 == libType: ##Continuous
      subDir += "lgE_{0:0.1f}/".format(self.corOpts.minLgE)
      subDir += "sin2_{0:0.1f}/".format(self.corOpts.minSin2)
    elif 1 == libType: ##Discrete
      # prettyEnergy = np.log10(self.corOpts.shower.energy) + 15
      # subDir += "lgE_{0:0.1f}/".format(prettyEnergy)
      # subDir += "Zen_{0:0.0f}/".format(self.corOpts.shower.zenith)

      subDir += "runID_{0}_eventID_{1}/".format(self.runID, self.eventID)

    subDir += self.corOpts.GetPrimaryName() + "/"

    return subDir



  def GetHeadDir(self):
    type = self.corOpts.GetLibraryType()
    startDir = ""

    if self.useTempDir:
      self.CheckDataLocationExists(self.tempdir)
      startDir += self.tempdir
    else:
      self.CheckDataLocationExists(self.datadir)
      startDir += self.datadir

    startDir += self.GetLibraryDirectory()

    startDir += self.SixDigitID() + "/"

    return startDir

  def PrintFileOrDirectory(self, flag):

    if flag == 'basedir':
        self.CheckDataLocationExists(self.basedir)
        print(self.basedir)

    elif flag == 'corsikadir':
      self.CheckDataLocationExists(self.corsikadir)
      print(self.corsikadir)

    elif flag == 'corsikaexe':
      if self.corOpts.thinning != True:
        if self.corOpts.parallel == True:
          location = self.corsikadir + self.corsikampi
          self.CheckDataLocationExists(location, isfile=True)
          print(location)
        else:
          location = self.corsikadir + self.corsikanothin
          self.CheckDataLocationExists(location, isfile=True)
          print(location)
      else:
        location = self.corsikadir + self.corsikaexe
        self.CheckDataLocationExists(location, isfile=True)
        print(location)

    elif flag == 'datadir':
      print(self.datadir)

    elif flag == 'tempdir':
      print(self.tempdir)

    elif flag == 'headdir':
      print(self.GetHeadDir())

    elif flag == 'condordir':
      startDir = "/data/sim/IceCubeUpgrade/CosmicRay/Radio/coreas/data/"
      startDir += self.GetLibraryDirectory()
      print(startDir)

    elif flag == 'inpfile':
      print(self.GetInpFileName())

    elif flag == 'logfile':
      print(self.GetLogFileName())

    elif flag == 'longfile':
      print(self.GetLongFileName())

    elif flag == 'id':
      print(self.SixDigitID())

  def GetLogFileName(self):
    return self.GetHeadDir() + "SIM" + self.SixDigitID() + ".log"

  def GetInpFileName(self):
    return self.GetHeadDir() + "SIM" + self.SixDigitID() + ".inp"

  def GetReasFileName(self):
    return self.GetHeadDir() + "SIM" + self.SixDigitID() + ".reas"

  def GetListFileName(self):
    return self.GetHeadDir() + "SIM" + self.SixDigitID() + ".list"

  def GetLongFileName(self):
    return self.GetHeadDir() + "DAT" + self.SixDigitID() + ".long"

  def ParseArguments(self):
    import argparse
    parser = argparse.ArgumentParser(description='Variable class for CORSIKA')
    parser.add_argument('--temp', action='store_true')
    parser.add_argument('--runID', type=int)#, required=True)
    parser.add_argument('--eventID', type=int)#, required=True)
    args, unknown = parser.parse_known_args()

    self.runID = args.runID
    self.eventID = args.eventID
    self.useTempDir = args.temp
    self.corOpts.ParseArguments()
