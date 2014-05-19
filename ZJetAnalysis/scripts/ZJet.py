#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import argparse
#import ZJet.ZJetAnalysis.zjetConfigBase as zjetConfigBase
import ZJet.ZJetAnalysis.x as x
import Artus.Utility.logger as logger
log = logging.getLogger(__name__)


import sys
from Artus.Configuration.artusWrapper import ArtusWrapper


if __name__ == "__main__":

	#Additional ZJet parser arguments
	zjetParser = argparse.ArgumentParser(add_help=False)
	zjetGroup = zjetParser.add_argument_group("ZJet options")
	zjetGroup.add_argument('-y', '--year', type=int,
        default=2012,
        help="data taking period. Default ist %(default)s")

	artusWrapper = ArtusWrapper("ZJet", [zjetParser])

	conf = artusWrapper.getConfig()

	#Get additional Zjet settings from config base
	#zjetconf = zjetConfigBase.getZjetConfig(conf)
	#conf.update(zjetconf)
	print conf
	sys.exit()

	artusWrapper.setConfig(conf)

	# Run the wrapper
	sys.exit(artusWrapper.run())

