#!/bin/bash

if [[ $1 == "" ]]; then
  echo "You must give in parameters to this script"
  echo "SubmitCtrl.sh <ID> <Python flags>"
  exit 1
fi

HOST=$(hostname -s)

ONCONDOR=0

if [[ $HOST == asterix* ]]; then
  echo "Submitting from Asterix"
  ONASTERIX=1
elif [[ $HOST == login* ]] || [[ $(hostname -d) == "localdomain.hpc.udel.edu" ]]; then
  echo "Submitting from Caviness"
  vpkg_require gcc/9.1
  vpkg_require binutils/2.33.1
  vpkg_require python/3.7.4
  ONCAVINESS=1
elif [[ $(hostname -d) == "icecube.wisc.edu" ]]; then
  echo "Submitting from Condor"
  ONCONDOR=1
  eval `/cvmfs/icecube.opensciencegrid.org/py3-v4.1.0/setup.sh`
else
  echo "I dont' know where you are!"
  echo "hostname -s" $(hostname -s)
  echo "hostname -d" $(hostname -d)
  echo "I will try to carry on, but who knows what will happen!\n"
fi

HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
echo "HERE: " $HERE
if [[ ! -f $HERE/SubmitCtrl.sh ]]; then
  HERE=$(dirname "$0")
fi

FLAGS=$@

source ~/.bashrc

QUERY_PY=$HERE/../Query.py

echo "Query.py is at $QUERY_PY"
BASEDIR=$($QUERY_PY --dir basedir)
EXEDIR=$($QUERY_PY --dir corsikadir)
EXE=$($QUERY_PY $FLAGS --dir corsikaexe)
TEMPDIR=$($QUERY_PY $FLAGS --dir headdir)
CORSIKA_ID=$($QUERY_PY $FLAGS --dir id)

echo "BASEDIR = $BASEDIR"
echo "EXEDIR = $EXEDIR"
echo "EXE = $EXE"
echo "TEMPDIR = $TEMPDIR"
echo "CORSIKA_ID = $CORSIKA_ID"

#Don't make the same file if it already exists on the Madison cluster
if [[ $FLAGS == *"--movetocondor"* ]]; then
  if [[ $(whoami) = alanc ]] || [[ $(whoami) = acoleman ]] || [[ $(whoami) = coleman ]]; then
    CONDORDIR=$($QUERY_PY $FLAGS --dir condordir)
    echo CONDORDIR = $CONDORDIR
    if ssh acoleman@data.icecube.wisc.edu stat $CONDORDIR/$CORSIKA_ID \> /dev/null 2\>\&1; then
      echo "Found existing $CONDORDIR/$CORSIKA_ID"
      echo "The file already exists on the cluster. I will not make it again. Terminating!"
      exit 1
    fi
  fi
fi

cd $BASEDIR

#In case is already exists we have to remove it or else CORSIKA will get sad
if [[ -d "$TEMPDIR" ]]; then
  rm -r $TEMPDIR
fi

#Generate steering files for CORSIKA
./generateInp.py $FLAGS

echo ""
echo "Beginning CORSIKA/CoREAS simulation"
cd $EXEDIR

echo "$EXE < $($QUERY_PY $FLAGS --dir inpfile) > $($QUERY_PY $FLAGS --dir logfile)"
date
$EXE < $($QUERY_PY $FLAGS --dir inpfile) > $($QUERY_PY $FLAGS --dir logfile)
date

#Do a double check to make sure that the simulation completed properly
if [[ ! -d $TEMPDIR/SIM${CORSIKA_ID}_coreas ]]; then
  echo "I think the simulation did not complete!"
  echo "I cannot find $TEMPDIR/SIM${CORSIKA_ID}_coreas"
  # exit 1  #Alanfix
else
  echo " "
  echo "-----Simulation completed successfully!-----"
  echo " "
fi

cd $BASEDIR

XMAX=$(grep "PARAMETERS  " $($QUERY_PY $FLAGS --dir longfile) | awk '{print $5}')
echo "GH fit Xmax = $XMAX"
XMAX=10000
if [[ $($QUERY_PY $FLAGS --xmaxBelow $XMAX) == 1 ]]; then
  echo ""
  echo ""
  echo "Xmax is below ground. Will resimulate using CONEX."

  REMAKEDIR=$TEMPDIR/Remake/
  echo "Making dir: $REMAKEDIR"
  mkdir $REMAKEDIR

  cp $TEMPDIR/*.reas $REMAKEDIR/.
  touch $REMAKEDIR/SIM${CORSIKA_ID}.list  #Only need a single antenna to reduce computation
  awk -v dir=$REMAKEDIR '{if($1 == "CASCADE") print "CASCADE T T T"; else if($1 == "DIRECT") print "DIRECT", dir; else if($1 == "OBSLEV") print "OBSLEV 0"; else print $0}' $TEMPDIR/*.inp > $REMAKEDIR/SIM${CORSIKA_ID}.inp

  cd $EXEDIR
  echo "$EXE < $REMAKEDIR/SIM${CORSIKA_ID}.inp > $REMAKEDIR/SIM${CORSIKA_ID}.log"
  date
  $EXE < $REMAKEDIR/SIM${CORSIKA_ID}.inp > $REMAKEDIR/SIM${CORSIKA_ID}.log
  date
  cd $BASEDIR

  XMAX=$(grep "PARAMETERS  " $REMAKEDIR/*.long | awk '{print $5}')
  echo "After rerun, XMAX is $XMAX"

  mv $($QUERY_PY $FLAGS --dir longfile) $TEMPDIR/backuplong.txt
  mv $($QUERY_PY $FLAGS --dir logfile) $TEMPDIR/backuplog.txt
  cp $REMAKEDIR/DAT${CORSIKA_ID}.long $($QUERY_PY $FLAGS --dir longfile)
  cp $REMAKEDIR/*.log $($QUERY_PY $FLAGS --dir logfile)
  rm -r $REMAKEDIR

else
  echo "Xmax seems ok..."
fi



#If you were using the temp directory, move to the final directory
FLAGS_NO_TEMP=$(echo ${FLAGS/--temp/})
FINALDIR=$($QUERY_PY $FLAGS_NO_TEMP --dir headdir)

if [[ $FLAGS == *" --temp"* ]]; then
  echo "Moving directory $TEMPDIR to $FINALDIR"

  #Do a copy instead of a remove in case it fails in the middle
  if [[ -d "$FINALDIR" ]]; then
    rm -r $FINALDIR
  fi

  mkdir -p $FINALDIR

  cp -r $TEMPDIR/* $FINALDIR
  rm -r $TEMPDIR
fi

if [[ $FLAGS == *"--movetocondor"* ]]; then

  if [[ $(whoami) = alanc ]] || [[ $(whoami) = acoleman ]] || [[ $(whoami) = coleman ]]; then

    CONDORDIR=$($QUERY_PY $FLAGS --dir condordir)

    echo "Will move to condor directory" $CONDORDIR

    if ssh acoleman@data.icecube.wisc.edu stat $CONDORDIR/ \> /dev/null 2\>\&1; then
      echo "Its there!"
    else
      echo "Making the target directory"
      ssh acoleman@data.icecube.wisc.edu mkdir -p $CONDORDIR
    fi

    if [[ $ONCONDOR == 1 ]]; then
      echo "You are on Condor, moving directly"

      if [[ ! -d $CONDORDIR ]]; then
        mkdir -p $CONDORDIR
      fi

      rsync -auP $FINALDIR/. $CONDORDIR/ > /dev/null 2>&1
      rm -r $FINALDIR
    else
      #Let the transfer cronjobs know that this file is complete
      echo "This file is ready for transfer"
      echo $CONDORDIR/$CORSIKA_ID > $FINALDIR/Ready
    fi

  else
    echo "You do not have the credentials to move the files to condor!"
  fi
fi
