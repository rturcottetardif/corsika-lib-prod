#!/usr/bin/python3

import numpy as np
from icecube import dataio, radcube
from icecube.icetray import I3Frame, I3Units
from icecube.dataclasses import I3Constants, I3Position
from icecube.icetray.i3logging import log_warn, log_info, log_fatal
import extractI3Variables as i3var


# ANTENNA HEIGHT IS 2838m
antennaHeight = 2840 * I3Units.m # FOR STAR (==ObsLevel)
# antennaHeight = 2832.19 * I3Units.m # FOR ARRAY
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.set_xlabel("zenith / degree")
ax.set_ylabel("log(E_rox) - log(E_stef)")
ax.set_ylim(-1, 1)

def aziI3ParticleToCoREAS(azimuth):
    return (azimuth / I3Units.deg - radcube.GetMagneticRotation() / I3Units.deg + 180)*I3Units.deg


def moveCoreToAntennaLevel(i3PartPos, i3PartDir):
    return i3PartPos + i3PartDir * ((i3PartPos.z + I3Constants.OriginElev - antennaHeight)/np.cos(i3PartDir.zenith))
    # return i3PartPos - i3PartDir * ((i3PartPos.z + I3Constants.OriginElev - antennaHeight) / i3PartDir.z)

def formatingArray(unixTime, runId, eventId, zenith, azimuth,
                   energy, coreX_antennaLev, coreY_antennaLev, coreZ_antennaLev):
    # Direction in degree
    # Position in m
    # Energy in PeV
    sim_prop = np.array((unixTime, runId, eventId, zenith, azimuth, energy,
                         coreX_antennaLev, coreY_antennaLev, coreZ_antennaLev),
                 dtype=([('time', np.int32), ('runId', np.int32), ('eventId', np.int32),
                         ('zenith', np.float32), ('azimuth', np.float32), ('energy', np.float32),
                         ('coreX_Ant', np.float32), ('coreY_Ant', np.float32), ('coreZ_Ant', np.float32)]))
    return sim_prop


def getInfoForSim(frame):
    runId, eventId = i3var.getRunIdEventIdfromI3File(frame)
    if frame.Has('TaxiTime'):
        unixTime = frame['TaxiTime'].unix_time
    elif frame.Has('RadioTaxiTime'):
        unixTime = frame['RadioTaxiTime'].unix_time
    else:
        log_fatal("Your frame doesn't have time for radio")

    ## IceTop reconstruction
    energy_old = i3var.getIceTopEnergy(frame) / I3Units.PeV
    print("my first shitty energy reco: ", energy_old)
    # better reco from Stef!
    energy = frame["energy_estimate2"].value / I3Units.PeV  #In GeV in the frame
    print("new energy reco from Stef: ", energy)

    I3Part = frame["Laputop"]

    if args.conversion:
        print("saving the infos converted to CoREAS...")
        print("Core reconstructed by IT, ", I3Part.pos)
        print("Direction reco by IT", I3Part.dir)

        # We rotate the raised The Azimuth form IC to CoREAS and save them outside
        zen = I3Part.dir.zenith / I3Units.degree
        azi = aziI3ParticleToCoREAS(I3Part.dir.azimuth) / I3Units.degree

        # The direction and position are in IC Coord.
        # We raise the IC core to the antenna level
        print("z height IT", I3Part.pos.z + I3Constants.OriginElev)
        I3Part.pos = moveCoreToAntennaLevel(I3Part.pos, I3Part.dir)
        print("after", I3Part.pos)

        # transfo to CoREAS ref. system
        I3Part.pos.rotate_z(-radcube.GetMagneticRotation())
        print("Core in North-West coord. system ", I3Part.pos)

        core_Ant = I3Part.pos
        coreX = core_Ant.x / I3Units.m
        coreY = core_Ant.y / I3Units.m
        # Put the core at the antenna level
        coreZ = (core_Ant.z + I3Constants.OriginElev) / I3Units.m
        print("saving core: ", coreX, coreY, coreZ)
        print("saving dir: ", zen, azi)

    else:
        print("I get directly the IceTop reconstruction...")
        zen = I3Part.dir.zenith / I3Units.degree
        azi = I3Part.dir.azimuth / I3Units.degree
        core_Ant = I3Part.pos
        coreX = core_Ant.x / I3Units.m
        coreY = core_Ant.y / I3Units.m
        coreZ = (core_Ant.z + I3Constants.OriginElev) / I3Units.m


    ax.scatter(zen, np.log10(energy_old)-np.log10(energy), c="k", alpha=0.5)


    sim_prop = formatingArray(unixTime, runId, eventId, zen, azi, energy, coreX, coreY, coreZ)

    # infos = np.array((unixTime, runId, eventId, zen, azi, energy, core_IT.x, core_IT.y, core_IT.z, coreX, coreY, coreZ),
    #                  dtype=([('time', np.int), ('runId', np.int), ('eventId', np.int),
    #                          ('zenith', np.float32), ('azimuth', np.float32), ('energy', np.float32),
    #                          ('coreX_IT', np.float32), ('coreY_IT', np.float32), ('coreZ_IT', np.float32),
    #                          ('coreX_Ant', np.float32), ('coreY_Ant', np.float32), ('coreZ_Ant', np.float32)]))
    return sim_prop


# save the shower file in .npy for a given i3File
def saveNpyWithGivenI3File(outputName, I3File):
    with open(outputName, 'wb') as f:
        in_file = dataio.I3File(I3File, 'r')
        for frame in in_file:
            if in_file.stream == I3Frame.Physics:
                info = getInfoForSim(frame)
                if (args.runid != 0) and (args.runid == info["runId"]):
                    print("saving....")
                    print(info)
                    np.save(f, np.array(info))
                    break
                elif args.runid == 0:
                    print("====================")
                    print(info)
                    np.save(f, np.array(info))
                    # np.save(f, np.array(info))
                    # Very ugly hack to get it running
                else:
                    print("::WARNING:: you want a runID that I don't have in the i3 file you provided me....")
    plt.savefig("Energies.png")

# save the shower file in .npy for a given i3File
def saveNpy(outputName, sim_properties, write_mode='wb'):
    with open(outputName, write_mode) as f:
        np.save(f, np.array(sim_properties))
    print("I create a new file : ", outputName)


# How to read the npy file
def readNpy(filename):
    events = []
    with open(filename, 'rb') as f:
        try:
            while 1:
                events.append(np.load(f))
        except ValueError: # a bit of a sketchy fix
            print("EoF")
    return events


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str,
                        help='file with showers')
    parser.add_argument('output', type=str, default="/data/user/rturcotte/showers/showers.npy",
                        help='output name of the file with showers info')
    parser.add_argument('--conv', dest='conversion', action='store_true',
                        help='Convert the core and direction from IceCube to CoREAS')
    parser.add_argument("--runid", type=int, default=0)
    parser.set_defaults(conversion=True)
    args = parser.parse_args()

    showerFile = args.input
    filename = args.output
    saveNpyWithGivenI3File(filename, showerFile)
