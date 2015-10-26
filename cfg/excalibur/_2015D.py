import configtools


def modify_config(cfg):
	"""
	Use 2015D data only
	"""
	cfg['JsonFiles'].add_run_range(256629, float("inf"))
	if cfg['InputIsData']:
		cfg["InputFiles"] = configtools.setInputFiles(
			ekppath="/storage/a/mfischer/skims/zjet/2015-10-09/DoubleMu_Run2015D_Sep2015_13TeV/*.root",
			nafpath="/pnfs/desy.de/cms/tier2/store/user/mafische/skims/MF_AnyMu_2015_746/2015-10-09/DoubleMu_Run2015D_Sep2015_13TeV/*.root",
		)
		cfg['Lumi'] = configtools.get_lumi(json_source=cfg['JsonFiles'])
	return cfg
