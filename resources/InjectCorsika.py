#!/usr/bin/env python
## -------------------------------------------------------------------------------------------------
## Script for running Scintillators and IceTop's tank response with most of the parameters
## set as default ->> you can look them up in segment --> segmentITEXDefault 
## -------------------------------------------------------------------------------------------------
import sys
from optparse import OptionParser, IndentedHelpFormatter
from icecube.surface_sim_scripts.segments.segmentITExDefault import SimIceTopScint
from icecube.surface_sim_scripts import radiotools
from icecube.radcube import defaults

from icecube.icetray.i3logging import *


parser = OptionParser(formatter=IndentedHelpFormatter(indent_increment=4, max_help_position=60))
parser.add_option("-o", "--output", action="store", dest="output",
                  help="Output file name (with extension .i3, .i3.gz)", metavar="FILE")
parser.add_option("--gcd", action="store", dest="gcd", help="GCD file",
                  metavar="gcd_file")
parser.add_option("-s", action="store", type="int", dest="samples",
                  help="Number of times each shower is sampled. Default: 1", metavar="S", default=1)
parser.add_option("-x", action="store", type="float", dest="x",
                  help="The shower's x-coordinate. Default: 0", metavar="X", default=0)
parser.add_option("-y", action="store", type="float", dest="y",
                  help="The shower's y-coordinate. Default: 0", metavar="Y", default=0)
parser.add_option("-r", action="store", type="float", dest="r",
                  help="Radius of a circular sampling region for the core location around (x,y). Default: 0", metavar="R", default=0)
parser.add_option("--seed", action="store", type="int", dest="seed",
                  help="Seed for random number generator. Default: 0", default=0)
parser.add_option('--run_id', type=int, default=1, metavar='NUM', help='an arbitrary run number')
parser.add_option('--no_ice_top', default=False, action="store_true", help='If set, IT simulation will not be done')

(options, infiles) = parser.parse_args()
options = vars(options)

#Save this for later so we can pass in **kargs to the segment
output = options['output']
del options['output']

if len(infiles) != 1:
    print('You can only give one input file')
    parser.print_help()
    sys.exit(1)

corsikaFile = infiles[0]

#Get the (fixed) location of the radio core
radX, radY, directory = radiotools.GetCoreFromReasFile(corsikaFile)

#Quick check for errors in reading the .reas file
if radiotools.UNDEF == radX or radiotools.UNDEF == radY:
  log_fatal("Skipping event {0}".format(corsikaFile))

# Set fixed core location
options['x'] = radX
options['y'] = radY


# def SimulateSingleEvent(corsikaFile, directory, output):
from I3Tray import I3Tray
from icecube import dataclasses, simple_veto
from icecube import icetray, dataio, radcube

tray = I3Tray()

tray.AddSegment(SimIceTopScint, 'SimIceTopScint', 
                input=[corsikaFile],
                **options)

ElectronicServiceName = defaults.CreateDefaultElectronicsResponse(tray)
AntennaServiceName = defaults.CreateDefaultAntennaResponse(tray)

tray.AddModule("CoreasReader", "CoreasReader",
               DirectoryList=[directory],
               MakeGCDFrames=False,
               AddToExistingGCD=False,
               MakeDAQFrames=False,
               PiggybackMode=True,
              )

tray.AddModule("ZeroPadder", "ZeroPadder",
               InputName=radcube.GetDefaultSimEFieldName(),
               OutputName="ZeroPaddedMap",
               ApplyInDAQ = True,
               AddToFront = True,
               AddToTimeSeries = True,
               FixedLength = 5000
              )

tray.AddModule("ChannelInjector", "ChannelInjector",
                InputName="ZeroPaddedMap",
                OutputName="RawVoltageMap",
                AntennaResponseName=AntennaServiceName
              )

tray.AddModule("TraceResampler", "Resampler",
               InputName="RawVoltageMap",
               OutputName="ResampledVoltageMap",
               ResampledBinning=defaults.resampledBinning                #Inverse sampling frequency
              )



 
tray.AddModule('Delete', 'Delete',
  Keys=['HitBinWidth','BeaconLaunches',
  'MCTimeIncEventID', 'RNGState',
  'IceTopCalibratedWaveformRange',
  'InIceRawData','ZeroPaddedMap', 'RawVoltageMap'],
  KeyStarts=['CalibratedIceTop', 'IceTopComponentWaveforms'])
  
##################Writing output of simulations####################
tray.AddModule("I3Writer", "i3-writer",
              Filename = output,
              streams = [icetray.I3Frame.TrayInfo,
              icetray.I3Frame.DAQ,
              icetray.I3Frame.Physics]
              )

tray.AddModule("TrashCan", "trashcan")
tray.Execute()
tray.Finish()


print("\n\n\n",str(directory) + "-->" + str(output),"\n\n\n")