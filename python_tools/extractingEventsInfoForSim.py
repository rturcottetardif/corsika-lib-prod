#!/usr/bin/python3

import numpy as np
from icecube import dataio, radcube
from icecube.icetray import I3Frame, I3Units
import importlib.util
spec = importlib.util.spec_from_file_location(
    "showerEnergy", "/home/rturcotte/work/scripts/showerEnergy/utils/extractI3Variables.py")
i3var = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i3var)

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('input', type=str, nargs='+', default=[],
                    help='List of files with showers')
parser.add_argument('--output', type=str, default="/data/user/rturcotte/showers/showers.npy",
                    help='output name of the file with showers info')
args = parser.parse_args()


def aziI3ParticleToCoREAS(azimuth):
    return (azimuth / I3Units.deg - radcube.GetMagneticRotation() / I3Units.deg + 180)*I3Units.deg


def getInfoForSim(frame):
    runId, eventId = i3var.getRunIdEventIdfromI3File(frame)
    unixTime = frame['TaxiTime'].unix_time
    zen = i3var.getIceTopZenith(frame) / I3Units.degree
    azi = aziI3ParticleToCoREAS(i3var.getIceTopAzimuth(frame)) / I3Units.degree
    energy = i3var.getIceTopEnergy(frame) / I3Units.PeV
    coreX, coreY = i3var.getIceTopCore(frame)
    coreZ = i3var.getIceTopHeight(frame)
    infos = np.array((unixTime, runId, eventId, zen, azi, energy, coreX, coreY, coreZ),
                     dtype=([('time', np.int), ('runId', np.int), ('eventId', np.int),
                             ('zenith', np.float32), ('azimuth', np.float32), ('energy', np.float32),
                             ('coreX', np.float32), ('coreY', np.float32), ('coreZ', np.float32)]))
    return infos


showerFile = args.input
filename = args.output

with open(filename, 'wb') as f:
    in_file = dataio.I3File(showerFile[0], 'r')
    for frame in in_file:
        if in_file.stream == I3Frame.DAQ:
            np.save(f, np.array(getInfoForSim(frame)))

## How to read the npy file
# with open(filename, 'rb') as f:
#     try:
#         while 1:
#             event = np.load(f)
#     except ValueError: # a bit of a sketchy fix
#         print("EoF")
