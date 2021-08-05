#import matplotlib
#matplotlib.use('Agg')
#import matplotlib.pyplot as plt
#import matplotlib.gridspec as gridspec
#import matplotlib.patches as mpatches

#import matplotlib.cm as cm

import numpy as np

from .CorsikaOptions import CorsikaOptions
from .RadtoolsCoordSys import cstrafo

class StarGenerator(object):
  def __init__(self):
    self.zenithAngle = 0.
    self.azimuthAngle = 0.

    self.radii = []

    ###If set to true, will use the spacing according to a parameterization of
    ###the Cherenkov ring location. Otherwise, will use values fixed below
    self.useRingParam = True

    ###If you want to use the fixed grid spacing, set these values
    self.spacing = [0.5, 50, 25, 50, 100] #spacing in meters
    self.maxRad = [0.5, 100.5, 250.5, 300.5, 1000.5] #Break points for spacings

    ###If you want to used a parameterized ring, use these values
    self.ringDensity = 10
    self.spokes = 8.

    self.antennaList = []

    self.corOpts = CorsikaOptions()

  def SetRadii(self, spacing, maxRad):
    self.spacing = spacing
    self.maxRad = maxRad

  def SetNSpokes(self, n):
    self.spokes = n

  def GenerateCircle(self):

    self.antennaList.clear()

    dTheta = 2* np.pi / self.spokes

    for itheta in range(int(self.spokes)):

      theta = dTheta * itheta

      irad = 0
      rad = self.spacing[irad]

      while rad <= self.maxRad[-1] and irad < len(self.maxRad):
        self.antennaList.append([rad, theta])
        rad += self.spacing[irad]

        if rad > self.maxRad[irad]:
          rad -= self.spacing[irad]

          irad += 1
          if irad >= len(self.maxRad):
            break

          rad += self.spacing[irad]


  def SecDeg(self, deg):
    return 1. / np.cos(deg * np.pi / 180.)


  def GetRingCenter(self, zenith):
    sec = self.SecDeg(zenith)

    #Only tuned down to here
    if sec < self.SecDeg(45):
      sec = self.SecDeg(45)

    return -3.766 * sec**2 + 154.5 * sec - 134.6


  def GetRingWidth(self, zenith):
    #The "sigma" of the width
    sec = self.SecDeg(zenith)

    #Only tuned down to here
    if sec < self.SecDeg(45):
      sec = self.SecDeg(45)

    #Only tuned up to here
    if sec > self.SecDeg(86):
      sec = self.SecDeg(86)

    return -10.59 * sec**2 + 239.4 * sec - 36.27


  def GenerateCircleFromFunction(self, zenithAngle):
    self.antennaList.clear()

    center = self.GetRingCenter(zenithAngle)
    fwhm = self.GetRingWidth(zenithAngle)

    maxRad = max(min(2500, center + fwhm), 450) #Put hard cuts on max radius
    minRad = 0.01 #Guarantee one at the center
    self.spacing = np.linspace(minRad, maxRad, self.ringDensity*2)

    dTheta = 2* np.pi / self.spokes
    for itheta in range(int(self.spokes)):

      theta = dTheta * itheta

      for rad in self.spacing:
        self.antennaList.append([rad, theta])

  def ConvertToCartesian(self):
    for ival, val in enumerate(self.antennaList):
      r = val[0]
      theta = val[1]
      self.antennaList[ival] = [r * np.cos(theta), r * np.sin(theta)]

  def StretchCircle(self, angle):
    for ival, val in enumerate(self.antennaList):
      x = val[0]
      y = val[1]
      self.antennaList[ival] = [x / np.cos(angle), y]

  def RotateCircle(self, angle):
    for ival, val in enumerate(self.antennaList):
      x = val[0]
      y = val[1]
      self.antennaList[ival] = [x * np.cos(angle) - y * np.sin(angle), x * np.sin(angle) + y * np.cos(angle)]

  def ConvertToCorsika(self, zenith, azimuth):
    magneticVector = np.array([self.corOpts.magneticHorizontal, 0, self.corOpts.magneticUp])
    converter = cstrafo(zenith * np.pi / 180., azimuth * np.pi / 180. - np.pi, magnetic_field_vector=magneticVector)
    self.antennaList = converter.transform_from_vxB_vxvxB_2D(np.array(self.antennaList))

  #Give angles in degrees to me!!!
  def GenerateList(self, zenithAngle, azimuthAngle):
    if self.useRingParam:
      self.GenerateCircleFromFunction(zenithAngle)
    else:
      self.GenerateCircle()  #Makes the basic ring

    self.ConvertToCartesian()  #Converts from polar to x/y
    self.ConvertToCorsika(zenithAngle, azimuthAngle)
    # self.StretchCircle(zenithAngle * np.pi / 180.)
    # self.RotateCircle(azimuthAngle * np.pi / 180. + np.pi)

  def GetAntennaList(self):
    return self.antennaList

#  def PlotAntennaList(self):
#    fig = plt.figure()
#    ax = fig.add_subplot(1,1,1)


#    colors = cm.rainbow(np.linspace(0, 1, len(self.antennaList)))

#    ax.scatter(np.array(self.antennaList)[:,0], np.array(self.antennaList)[:,1], color=colors)
#    ax.set_aspect('equal')
#    ax.set_xlabel("Grid East [m]")
#    ax.set_ylabel("Grid North [m]")

#    fig.savefig("StarPattern.pdf")

  def MakeListFile(self, filename):
    file = open(filename, "w")

    for i in range(len(self.antennaList)):
      x = self.antennaList[i][0] * 1.e2
      y = self.antennaList[i][1] * 1.e2
      stnID = int(i + 1)
      file.write("AntennaPosition = {0:.2f} \t{1:.2f} \t{2:.2f} \tant_{3}\n".format(x, y, self.corOpts.antennaHeight, stnID))

    file.close()
    print("\tMade star-pattern listfile", filename)



# star = StarGenerator()
# star.GenerateList(40,0)
# print(len(star.GetAntennaList()))
# star.PlotAntennaList()
# star.MakeListFile("TestList.list")
