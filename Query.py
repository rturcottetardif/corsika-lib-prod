#!/usr/bin/env python3

import python_tools

import argparse
parser = argparse.ArgumentParser(description='Variable class for CORSIKA')
parser.add_argument('--dir', type=str, default="", required=False)
parser.add_argument('--xmaxBelow', nargs=2, type=float, required=False)
args, unknown = parser.parse_known_args()

handler = python_tools.FileHandler.FileHandler()
handler.ParseArguments()

if args.dir != "":
  handler.PrintFileOrDirectory(args.dir)

elif args.xmaxBelow != -1:
  print(handler.corOpts.XmaxBelowGround(args.xmaxBelow[0], args.xmaxBelow[1]))

else:  

  print("Corsika head dir......", handler.corsikadir)
  print("Corsika default exe...", handler.corsikaexe)
  print("Corsika no thinning...", handler.corsikanothin)
  print("Corsika MPI exe.......", handler.corsikampi)
  print("\nTemp dir..............", handler.tempdir)
  print("Data dir..............", handler.datadir)
  print("Log-file dir..........", handler.logfiledir)
