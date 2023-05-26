#!/usr/bin/env python3

# import sys
# from sys import argv
import numpy as np
import os
import math
from shutil import copyfile

from python_tools.FileHandler import FileHandler
from python_tools.StarPattern import StarGenerator

handler = FileHandler()
handler.ParseArguments()


print("\n============================================")
print("===============generateInp.py===============")
print("============================================")

print("Event Number: ", handler.corOpts.eventID)

handler.corOpts.RandomizeShower() #Will randomize only the variables needed
handler.corOpts.shower.PrintShowerVariables()

print("The antenna observation level is", handler.corOpts.antennaHeight * 0.01,"[m]")
print("The CORSIKA observation level is", handler.corOpts.obslev * 0.01,"[m]")

if handler.corOpts.useStar:
  print("Using the star-shaped pattern")
else:
  print("Generating surface extension layout")

headdir = handler.GetHeadDir()
print("Making files in", headdir)
print("============================================\n")

if not os.path.exists(headdir):
  print("\tMaking head dir", headdir)
  os.makedirs(headdir)


#########################Creating .inp file#####################################

print("Generating steering file...")
inp_name = handler.GetInpFileName()
print("Filename:", inp_name)

file = open(inp_name, 'w')
seed1 = handler.corOpts.seed
seed2 = handler.corOpts.seed + 1000000
seed3 = handler.corOpts.seed + 2000001
seed4 = handler.corOpts.seed + 3000002

#Thinning parameters, max weight = Energy [GeV] * thinning parameter
thinningVal = 1.e-6
maxWeight = (handler.corOpts.shower.energy * 1.e6) * thinningVal

file.write('RUNNR       {0}\n'.format(handler.corOpts.eventID))
file.write('EVTNR       1\n')
file.write('SEED        {0}    0    0\n'.format(seed1)) # seed for hadronic part
file.write('SEED        {0}    0    0\n'.format(seed2)) # seed for EGS4 part
file.write('SEED        {0}    0    0\n'.format(seed3)) # seed for Cherenkov part
file.write('NSHOW       1\n')
file.write('ERANGE      {0}e+6    {0}e+6\n'.format(handler.corOpts.shower.energy)) # in GeV
file.write('ESLOPE      -1.0\n')
file.write('PRMPAR      {}\n'.format(int(handler.corOpts.shower.primary)))
file.write('THETAP      {0:0.4f}    {0:0.4f}\n'.format(handler.corOpts.shower.zenith)) #
file.write('PHIP        {0:0.4f}    {0:0.4f}\n'.format(handler.corOpts.shower.azimuth)) ###If you want corsika to choose random azimuth, set azi1=-180 and azi2=180. Better to use this only if you have core(0,0) for radio

if handler.corOpts.thinning:
  file.write('THIN        {0}    {1}    0.0\n'.format(thinningVal, maxWeight))
  file.write('THINH       2.00E+02 10.000000\n')


else:
  print("REMEMBER TO ADD BACK IN MULTITHIN")
  # file.write('MTHINR      0.e2\n')
  # file.write('MTHINH      {0}    {1}      1.     1.\n'.format(thinningVal, maxWeight))
  # file.write('MSEED       {0}         0       0\n'.format(seed4))
  # file.write('MWEIC       1     F    use the thinning mode define by the first MTHINH line\n')

file.write('ECUTS       0.02     0.01    4.0E-04 4.00E-04\n')

if handler.corOpts.parallel:
  ecut = 1.E4
  emax = energy * 1.e-2
  if ecut >= emax:
    ecut = emax * 1.e-1
  file.write('PARALLEL    {0} {1} 1 F'.format(ecut, emax))

if not handler.corOpts.fastShowers:
  file.write('CASCADE     F F F\n')
elif handler.corOpts.fastShowers:
  file.write('CASCADE     T T T\n')
else:
  file.write('CASCADE     F F F\n')

file.write('ELMFLG      T    T\n')
file.write('OBSLEV      {0}\n'.format(handler.corOpts.obslev))
file.write('ECTMAP      1.e11\n')
file.write('SIBYLL      T    0\n')
file.write('SIBSIG      T\n')
file.write('FIXHEI      {0}    0\n'.format(handler.corOpts.fixHeight))
# file.write('FIXHEI      0.    0\n')
file.write('HADFLG      0    1    0    1    0    2\n')
file.write('STEPFC      1.0\n')
file.write('MUMULT      T\n')
file.write('MUADDI      T\n')
file.write('MAXPRT      1\n')
file.write('MAGNET      {0}  {1}\n'.format(handler.corOpts.magneticHorizontal, -1*handler.corOpts.magneticUp))  #Corsika expects negative z
file.write('LONGI       T     10.  T    T\n')
file.write('RADNKG      2.E5\n')
#file.write('ATMOD       33\n')

if handler.corOpts.realAtmos:
  file.write('ATMFILE     {0}atmos_runId{1}_eventId{2}.txt\n'.format(handler.atmosdir, handler.runID, handler.eventID))
else:
  file.write('ATMOD       33\n')

file.write('DIRECT      {0}\n'.format(headdir))#####change to required directory
file.write('USER        rturcotte\n')
file.write('EXIT\n')

file.close()


#########################Creating .reas file#####################################
reas_name = handler.GetReasFileName()
file2 = open(reas_name, 'w')

print("Creating .reas file...")
print("Filename:", reas_name)
print('\tCore at antenna level  ({0:0.2f}, {1:0.2f}, {2:0.2f}) [m]'.format(handler.corOpts.shower.coreX, handler.corOpts.shower.coreY, handler.corOpts.antennaHeight*1e-2))


#Need to project this up to the corsika observation level
thRad = handler.corOpts.shower.zenith*np.pi/180.
aziRad = handler.corOpts.shower.azimuth*np.pi/180.-np.pi
nUnit = [np.sin(thRad)*np.sin(aziRad), np.sin(thRad)*np.cos(aziRad), np.cos(thRad)] #Direction the shower is coming from


# if not handler.corOpts.proto:
  # antennaHeight = handler.corOpts.antennaHeight
#   # print("not proto, height ", antennaHeight)
# if handler.corOpts.proto:
#   antennaHeight = 283282    # Hard coded height of prototype Antennas
# #   print("proto, height ", antennaHeight)
# dCore = np.array(nUnit) * (handler.corOpts.obslev - antennaHeight) / np.cos(thRad)
dCore = [0, 0]

# Used to be that....
coreXToPrint = handler.corOpts.shower.coreX * 1.e2 + dCore[0]
coreYToPrint = handler.corOpts.shower.coreY * 1.e2 + dCore[1]

# coreXToPrint = handler.corOpts.shower.coreX * 1.e2
# coreYToPrint = handler.corOpts.shower.coreY * 1.e2

print('\tCore at CORSIKA OBSLEV ({0:0.2f}, {1:0.2f}, {2:0.2f}) [m]'.format(coreXToPrint*1e-2, coreYToPrint*1e-2, handler.corOpts.obslev*1e-2))

file2.write('# parameters setting up the spatial observer configuration:\n')
# Core at observation level
# Used to be that.....
# works for star but not array... Quite confused
# file2.write('CoreCoordinateNorth = {0}     ; in cm\n'.format(coreYToPrint))#####Specify core position x in corsika coordinates
# file2.write('CoreCoordinateWest = {0}     ; in cm\n'.format(coreXToPrint))#####Specify core position y in corsika coordinates

# That works for Array simulations but not start
file2.write('CoreCoordinateNorth = {0}     ; in cm\n'.format(coreXToPrint))#####Specify core position x in corsika coordinates
file2.write('CoreCoordinateWest = {0}     ; in cm\n'.format(coreYToPrint))#####Specify core position y in corsika coordinates


file2.write('CoreCoordinateVertical = {0}     ; in cm\n'.format(handler.corOpts.obslev))####Observation height
file2.write('\n')
file2.write('# parameters setting up the temporal observer configuration:\n')
file2.write('TimeLowerBoundary = -1 ; in s, only if AutomaticTimeBoundaries set to 0\n')
file2.write('TimeUpperBoundary = 1 ; in s, only if AutomaticTimeBoundaries set to 0\n')
file2.write('TimeResolution = 2e-10 ; in s\n')
file2.write('ResolutionReductionScale = 0 ; avoid that timing changes\n')
file2.write('AutomaticTimeBoundaries = 4.e-07 ; 0: off, x: automatic boundaries with width x in s\n')
file2.write('GroundLevelRefractiveIndex = 1.000292  ; specify refractive index at 0 m asl\n')
file2.write('CorsikaParameterFile = SIM'+str(handler.SixDigitID())+'.inp\n')
file2.close()


#########################Creating .list file#####################################
if handler.corOpts.proto:
  baseListName = handler.GetResourceDir() + "/BaseList_prototype.list"
else:
  baseListName = handler.GetResourceDir() + "/BaseList.list"
whereToPlace = handler.GetListFileName()
print("Making .list file...")
print("Filename:", whereToPlace)

if handler.corOpts.useStar:
  star = StarGenerator()
  star.GenerateList(handler.corOpts.shower.zenith, handler.corOpts.shower.azimuth)
  star.MakeListFile(whereToPlace)
else:
  print("Copying from:", baseListName)
  copyfile(baseListName, whereToPlace)

print("Finished generating input files for CORSIKA")
print("============================================")
print("============================================")
