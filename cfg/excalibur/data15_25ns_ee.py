import configtools


def config():
	cfg = configtools.getConfig('data', 2015, 'ee', bunchcrossing='25ns')
	cfg["InputFiles"].set_input(
		ekppath="/storage/a/mfischer/skims/zjet/2016-01-19/Zee_Zee_Run2015D-16Dec2015-v2/*.root",
		nafpath="",
	)
	cfg = configtools.expand(cfg, ['nocuts', 'zcuts', 'noalphanoetacuts', 'noalphacuts', 'noetacuts', 'finalcuts'], ['None', 'L1', 'L1L2L3', 'L1L2L3Res'])
	configtools.remove_quantities(cfg, ['jet1btag', 'jet1qgtag', 'jet1ptl1l2l3', 'jet1res', 'jet1rc', "e1mvanontrig", "e1mvatrig", "e2mvanontrig", "e2mvatrig"])
	return cfg
