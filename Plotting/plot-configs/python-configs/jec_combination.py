# -*- coding: utf-8 -*-

import time

import Excalibur.Plotting.harryinterface as harryinterface
import Artus.Utility.logger as logger

def jec_combination(args=None, additional_dictionary=None):
	"""function to create the root combination file for the jec group."""
	plots = []

	methoddict = {
		'ptbalance': 'PtBal',
		'mpf': 'MPF',
		'rawmpf': 'MPF-notypeI',
	}

	alpha_limits = [0.1, 0.15, 0.2, 0.3, 0.4]
	alpha_cuts = ['(alpha<{})'.format(limit) for limit in alpha_limits]
	alpha_strings = ['a'+str(int(100*limit)) for limit in alpha_limits]

	eta_borders = [0, 0.783, 1.305, 1.93, 2.5, 2.964, 3.139, 5.191]
	eta_cuts = ["({0}<=abs(jet1eta)&&abs(jet1eta)<{1})".format(*b) for b in zip(eta_borders[:-1], eta_borders[1:])]
	eta_cuts = ["(0<=abs(jet1eta)&&abs(jet1eta)<1.3)"] + eta_cuts # also include standard barrel jet selection
	eta_strings = ["eta_{0:0>2d}_{1:0>2d}".format(int(round(10*up)), int(round(10*low))) for up, low in zip(eta_borders[:-1], eta_borders[1:])]
	eta_strings = ["eta_00_13"] + eta_strings
	npv_weights = additional_dictionary.pop("_npv_weights",["1"])

	now = time.localtime()
	first = True
	for method in ['mpf', 'ptbalance', 'rawmpf']:
		for alphacut, alphastring in zip(alpha_cuts, alpha_strings):
			for etacut, etastring in zip(eta_cuts, eta_strings):
				for correction in ['L1L2L3']: # no L1L2L3Res available atm 
					labelsuffix = '_'.join([methoddict[method], 'CHS', alphastring, etastring, correction])
					eta_alpha_cut = '&&'.join((alphacut, etacut))
					d = {
						'x_expressions': ['zpt'],
						'y_expressions': [method],
						'x_bins': 'zpt',
						'analysis_modules': ['Ratio', 'ConvertToTGraphErrors'],
						'plot_modules': ['ExportRoot'],
						'tree_draw_options' : 'prof',
						'labels': ['_'.join([item, labelsuffix]) for item in ['Data', 'MC', 'Ratio']],
						'corrections': [correction],
						'filename': 'combination_ZJet_' + time.strftime("%Y-%m-%d", now),
						'file_mode': ('RECREATE' if first else 'UPDATE'),
						'weights': ["(%s)*(%s)" % (eta_alpha_cut, npv_weight) for npv_weight in npv_weights]
					}
					first = False
					if additional_dictionary is not None:
						d.update(additional_dictionary)
					plots.append(d)

	harryinterface.harry_interface(plots, args + ['--max-processes', '1'])


def jec_combination_20150722(args=None):
	d = {
		'files': [
			'ntuples/Data_13TeV_74X_E2_50ns_2015-07-22.root',
			'ntuples/MC_13TeV_74X_E2_50ns_algo_2015-07-22.root',
		],
		"algorithms": ["ak4PFJetsCHS",],
		# NPV hardcoded from Dominik's ``get_weights`` script output @ 20150722
		"_npv_weights" : ["1", "(npv==1)*60.7406+(npv==2)*4.00814+(npv==3)*5.16789+(npv==4)*4.87128+(npv==5)*4.18218+(npv==6)*3.43252+(npv==7)*3.26353+(npv==8)*2.78556+(npv==9)*2.65932+(npv==10)*2.02964+(npv==11)*1.64236+(npv==12)*1.30764+(npv==13)*1.17253+(npv==14)*0.901506+(npv==15)*0.687614+(npv==16)*0.636555+(npv==17)*0.366818+(npv==18)*0.318782+(npv==19)*0.21218+(npv==20)*0.148066+(npv==21)*0.104698+(npv==22)*0.0391752+(npv==23)*0.0121797+(npv==24)*0.0611739+(npv==25)*0.0192279+(npv==26)*0+(npv==27)*0+(npv==28)*0+(npv==29)*0+(npv==30)*0"],
	}
	jec_combination(args, d)