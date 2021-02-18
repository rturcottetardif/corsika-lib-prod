#!/usr/bin/python3

import numpy as np

class ShowerVariables(object):
  """docstring for ShowerVariables"""
  def __init__(self):
    
    self.zenith = 0
    self.azimuth = 0
    self.energy = 0.001
    self.primary = 14  #1-gamma, 14-proton, 5626-Iron
    self.coreX = 0.e2
    self.coreY = 0.e2

  def SetCore(self, x, y):
    self.coreX = x
    self.coreY = y

  def SetDirection(self, zen, azi):
    self.azimuth = azi
    self.zenith = zen


  def GetPrimaryName(self):
    if self.primary == 14:
      return "proton"
    elif self.primary == 5626:
      return "iron"
    elif self.primary == 1:
      return "photon"
    return "unknown"

  def ParseArguments(self):
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--primary', type=float, default=self.primary)
    parser.add_argument('-e', '--energy', type=float, default=self.energy, help='Energy in PeV')
    parser.add_argument('-z', '--zenith', type=float, default=self.zenith, help='Zenith angle in degrees')
    parser.add_argument('-a', '--azimuth', type=float, default=self.azimuth, help='Azimuth angle in degrees')
    args, unknown = parser.parse_known_args()

    self.primary = args.primary
    self.energy = args.energy
    self.zenith = args.zenith

  def PrintShowerVariables(self):
    print("-----Shower Variables-----")
    print("Core location: {0:0.2f} {1:0.2f} [m]".format(self.coreX, self.coreY))
    print("Zenith: {0:0.2f} deg,  Azimuth {1:0.2f} deg".format(self.zenith, self.azimuth))
    print("Energy: {0:0.2f} PeV, log(E/eV): {1:0.2f}".format(self.energy, np.log10(self.energy)+15))
    print("Primary: {}".format(self.GetPrimaryName()))
    print("--------------------------")
