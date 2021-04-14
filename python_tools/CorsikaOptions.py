#!/usr/bin/python3

import numpy as np
from . import ShowerVariables

CORSIKAOPT_NOT_SET=-999

class CorsikaOptions(object):
  """docstring for CorsikaOptions"""
  def __init__(self):

    self.eventID = 0

    self.antennaHeight = 2838.e2 #Altitude of the antennas
    self.obslev = 2840.e2 #Altitude of the CORSIKA OBSLEV

    self.magneticHorizontal = 16.75  ##Magnetic field along the ground [uT]
    self.magneticUp = 51.96  ## Magnetic field in the zenith [uT]
    self.magneticEast = -8.557
    self.magneticNorth = 14.399
    #Angle between IC coords and CORSIKA coords ~= 120.72 deg
    self.rotationAngle = np.arctan2(self.magneticNorth, self.magneticEast)

    self.useStar = False

    self.thinning = False
    self.realAtmos = False
    self.fastShowers = False
    self.parallel = False

    self.minAzi = 0.0
    self.maxAzi = 360.0
    self.useRandAzi = False

    self.minSin2 = CORSIKAOPT_NOT_SET
    self.maxSin2 = CORSIKAOPT_NOT_SET
    self.minZen = CORSIKAOPT_NOT_SET
    self.maxZen = CORSIKAOPT_NOT_SET
    self.useRandZen = False

    self.minLgE = CORSIKAOPT_NOT_SET
    self.energyIndex = -1
    self.dE = 0.1 #Bin width of random eng bins
    self.useRandEnergy = False

    self.seed = 0
    self.randRadius = 400.


  def GetPrimaryName(self):
    return self.shower.GetPrimaryName()


  def ParseArguments(self):
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--id', type=int, default=0, required=False)
    parser.add_argument('--thin', action='store_true', help='Thin the particle files')
    parser.add_argument('--parallel', action='store_true', help='Simulate over multiple cores')
    parser.add_argument('--usestar', action='store_true', help='Use the starshaped pattern')

    parser.add_argument('--minSin2', type=float, default=self.minSin2)
    parser.add_argument('--maxSin2', type=float, default=self.maxSin2)

    parser.add_argument('--randazi', action='store_true')

    parser.add_argument('--minLgE', type=float, default=self.minLgE)
    parser.add_argument('--dE', type=float, default=self.dE, help='Width of energy bin in lg(E/eV)')
    parser.add_argument('--energyIndex', type=float, default=self.energyIndex)

    parser.add_argument('--randRadius', type=float, default=self.randRadius)
    parser.add_argument('--realAtmosphere', action='store_true', help='uses a real atmosphere')
    parser.add_argument('--fastShowers', action='store_true', help='use CONEX in fast simulation')

    args, unknown = parser.parse_known_args()

    if (args.minSin2 != self.minSin2) != (args.maxSin2 != self.maxSin2):
      throw("You cannot set flag --minSin2 but not --maxSin2")

    self.eventID = args.id
    self.thinning = args.thin
    self.parallel = args.parallel
    self.useStar = args.usestar
    self.realAtmos = args.realAtmosphere
    self.fastShowers = args.fastShowers

    self.useRandAzi = args.randazi

    self.useRandZen = ((args.minSin2 != CORSIKAOPT_NOT_SET) or (args.maxSin2 != CORSIKAOPT_NOT_SET))
    if (args.minSin2 != CORSIKAOPT_NOT_SET) and (args.maxSin2 != CORSIKAOPT_NOT_SET): #Randomness set by sin2
      self.minSin2 = args.minSin2
      self.maxSin2 = args.maxSin2

    self.useRandEnergy = (args.dE != self.dE) or (args.minLgE != self.minLgE)
    self.minLgE = args.minLgE
    self.energyIndex = args.energyIndex
    self.dE = args.dE

    self.randRadius = args.randRadius
    if self.useStar:
      self.randRadius = 0.

    self.shower = ShowerVariables.ShowerVariables()
    self.shower.ParseArguments()


  def GetLibraryType(self):
    if self.useRandZen and self.useRandEnergy: #Continuous
      return 0
    if (not self.useRandAzi) and (not self.useRandZen) and (not self.useRandEnergy): #Discrete
      return 1

    print("ALAN YOU SHOULD FIGURE OUT WHAT YOU WANT THIS TO DO!")
    exit()


  def RandomizeShower(self):
    '''Will randomize the core, energy, dir, as needed
    the seed is set using the string so that there is reapeatablility'''
    import random
    random.seed("{}{}{}{}{}{}{}".format(self.eventID, self.minSin2, self.minLgE, self.minAzi, self.shower.zenith, self.shower.azimuth, self.shower.energy))
    self.seed = random.randint(0, 1e8)
    print("Random seed:", self.seed)

    if self.randRadius:
      r = np.sqrt(random.random()) * self.randRadius
      phi = np.pi * 2 * random.random()
      self.shower.coreX = r * np.cos(phi)
      self.shower.coreY = r * np.sin(phi)
    else:
      self.shower.coreX = 0.
      self.shower.coreY = 0.

    if self.useRandZen:
      sin2 = (self.maxSin2 - self.minSin2) * random.random() + self.minSin2
      self.shower.zenith = np.arcsin(np.sqrt(sin2)) * 180. / np.pi
    else:
      print("Zenith is not random")

    if self.useRandAzi:
      self.shower.azimuth = (self.maxAzi - self.minAzi) * random.random() + self.minAzi
    else:
      print("Azi is not random")

    if self.useRandEnergy:
      print("Picking a random value between", self.minLgE, "and", self.minLgE+self.dE)
      if self.energyIndex == -1:
        self.shower.energy = 10**((self.minLgE + random.random() * self.dE) - 15)
      else:
        eMax = 10**(self.minLgE + self.dE)
        a = eMax**(1 + self.energyIndex)
        eMin = 10**(self.minLgE)
        b = eMin**(1 + self.energyIndex)
        self.shower.energy = (random.random() * (a - b) + b)**(1/(1+self.energyIndex)) * 1e-15

  def XmaxBelowGround(self, xmax):
    xmax = float(xmax)

    cos = np.cos(self.shower.zenith * np.pi / 180.)
    verticalDepth = xmax * cos

    if verticalDepth > 690. - 30. / cos: #If below the ground (with 30g tolerance)
      # print("Is outside of 690 - {}".format(30. / cos))
      return 1

    return 0
