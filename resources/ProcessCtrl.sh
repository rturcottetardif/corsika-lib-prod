#!/usr/bin/bash

HOST=$(hostname -s)

if [[ $(hostname -d) == "icecube.wisc.edu" ]]; then
  echo "Submitting from Condor"
  eval `/cvmfs/icecube.opensciencegrid.org/py3-v4.1.0/setup.sh`
else
  echo "I dont' know where you are!"
  echo "hostname -s" $(hostname -s)
  echo "hostname -d" $(hostname -d)
  echo "I will try to carry on, but who knows what will happen!\n"
fi

source ~/.bashrc

VARIABLE_PY=$HERE/../util/variables.py
if [[ ! -f $VARIABLE_PY ]]; then
  VARIABLE_PY=$(find $HERE |grep variables.py |tail -1)
fi

echo "variables.py is at $VARIABLE_PY"

HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
echo "HERE: " $HERE

echo "Working on files in $1"

HEADDIR=$1
ID=$(python -c "print('{0:06}'.format($2))")
echo "ID is" $ID

if [[ ! -d $HEADDIR ]]; then
  echo "$HEADDIR is not a directory"
  exit 0
fi
if [[ ! -d $HEADDIR/$ID ]]; then
  echo "$HEADDIR is not a directory"
  exit 0
fi

CORSIKAFILE=$HEADDIR/$ID/DAT${ID}

if [[ ! -f $CORSIKAFILE ]]; then
  echo "I am not sure what is going on, could not find $CORSIKAFILE"
  exit 0
fi

echo Will process $CORSIKAFILE

ICETRAY_ENV=/home/acoleman/work/icecube-software/surface-array/build/env-shell.sh
PYTHON_SCRIPT=$HERE/InjectCorsika.py
FLAGS="--no_ice_top --gcd /home/acoleman/work/datasets/gcd-files/GCD-Simulation-AntennaScint.i3.gz"

outputDIR=$(python -c "print('$1'.split('coreas')[0])")coreas/i3-files/discrete/$(python -c "print('$1'.split('discrete')[1])")
echo OUTPUTDIR IS $outputDIR

if [[ ! -d $outputDIR ]]; then
  echo Making dir $outputDIR
  mkdir -p $outputDIR
fi

echo "The time at the start is" $(date)

SEED=$(python -c "print(abs(hash('$1')) %(10**5) * 1000 + int('$ID'))")


outputName=$outputDIR/${ID}.i3.gz
tempName=$outputDIR/temp_${ID}.i3.gz

if [[ -f $outputName ]]; then
  echo File $outputName already exists, skipping.
  exit 1
fi

if [[ -f $tempName ]]; then
  rm $tempName
fi

echo python $PYTHON_SCRIPT $FLAGS --seed $SEED --output $tempName $CORSIKAFILE
$ICETRAY_ENV python $PYTHON_SCRIPT $FLAGS --seed $SEED --output $tempName $CORSIKAFILE
mv $tempName $outputName

echo "The time at the end is" $(date)
