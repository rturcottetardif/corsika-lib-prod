# corsika-library-production
Package to create a library of CORSIKA/CoREAS simulations specifically for the South Pole. (In general, it could work for any location, but would require some work to change, for instance, the constants.)

These have been tested and will work on the Asterix (Udel), Caviness (Udel), Darwin (Udel), and cobalt (IC) clusters.

You need to first update the file `resources/DataLocations.txt` to point to a few directories, exes, etc.
* `DATA_DIR`: Where you intend your data to eventually live.
* `LOGFILE_DIR`: Where your log files from the simulations will go
* `TEMP_DIR`: You have the option to create the showers in a temporary directory ex: scratch and then move it to DATA_DIR later. This is that temp dir

* `CORSIKA_DIR`: Where your corsika install lives (note this is the run dir and not the head dir)
* `CORSIKA_EXE`: The compiled exe that you want to use. This should have thinning turned on

Currently this version is ONLY compatible with conex turned on because if Xmax is within 30grams/cm^2 of ground, the shower is run again with conex to get a proper xmax estimation.


To submit jobs, be on the submit node of the corresponding cluster and edit `MakeContinuousShowerLibrary.py` or `MakeDiscreteShowerLibrary.py` for which showers you want to submit. Note that you have to go to the bottom of these files to edit the showers. Then run these files as ex: `./MakeDiscreteShowerLibrary.py` and it will make submit scripts and submit them to the grid.
