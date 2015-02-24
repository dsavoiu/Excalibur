#!/bin/bash


# set the environment
export EXCALIBURPATH=$(readlink -e .)
export BOOSTPATH=$(ls ${VO_CMS_SW_DIR}/${SCRAM_ARCH}/external/boost/* -d | tail -n 1)
export BOOSTLIB=${BOOSTPATH}/lib/libboost_regex.so.${BOOSTPATH/*\//}
export KAPPAPATH=$EXCALIBURPATH/../Kappa
export KAPPATOOLSPATH=$EXCALIBURPATH/../KappaTools
export ARTUSPATH=$EXCALIBURPATH/../Artus
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$ARTUSPATH:$KAPPAPATH/lib:$KAPPATOOLSPATH/lib:$BOOSTPATH/lib
export PATH=$PATH:$EXCALIBURPATH/scripts
export PYTHONPATH=$PYTHONPATH:$EXCALIBURPATH/python
export USERPC=`who am i | sed 's/.*(\([^]]*\)).*/\1/g'`

# source Artus ini script
source $ARTUSPATH/Configuration/scripts/ini_ArtusAnalysis.sh

# Set some user specific variables
if [ $USER = "dhaitz" ]; then
    export EXCALIBUR_WORK=/storage/a/dhaitz/zjet
fi


# Use this to open a root file directly in the TBrowser
rot()
{
    ipython -i $EXCALIBURPATH/scripts/rot.py $@
}
