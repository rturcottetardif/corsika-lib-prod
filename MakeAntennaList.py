#!/usr/bin/env python
# -*- coding: utf-8 -*-

## NEEDS TO BE CALLED IN ICETRAY ENVIRONMENT
## Makes a baselist.list with an input GCD

from icecube import radcube, dataio
from icecube.icetray import I3Units
from icecube.dataclasses import I3Constants
from python_tools.FileHandler import FileHandler

handler = FileHandler()

GCDFile = "/data/user/rturcotte/gcd-files/GCD-AntennaSurvey_2020.06.15.i3.gz"


rotation_angle = radcube.GetMagneticRotation()
geoFile = dataio.I3File(GCDFile, "r")
frame = geoFile.pop_frame()
while not frame.Has("I3AntennaGeometry"):
    frame = geoFile.pop_frame()

antennaMap = frame["I3AntennaGeometry"].antennageo
file = open(handler.basedir+"/resources/BaseList_prototype.list", "w")
for ikey, antkey in enumerate(antennaMap.keys()):
    antNo = "ant_{0:d}_{1:d}".format(antkey.station+10000, antkey.antenna+99)
    posIC = antennaMap[antkey].position
    posIC.rotate_z(-1*rotation_angle)

    posX = posIC.x
    posY = posIC.y
    posZ = I3Constants.OriginElev + posIC.z + antennaMap[antkey].heightAboveSnow

    file.write("AntennaPosition = {0}    {1:.3f} {2:.3f} {3:.1f}\n".format(antNo, posX/I3Units.cm, posY/I3Units.cm, posZ/I3Units.cm, antNo))
file.close()
print("I finished making the antenna list")
