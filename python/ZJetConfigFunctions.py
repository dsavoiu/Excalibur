import ZJetConfigBase

def getBaseConfig(**kwargs):
	cfg = {
		'SkipEvents': 0,
		'EventCount': -1,
		'Processors': [],
		'InputFiles': [],	 # overridden by artus
		'OutputPath': 'out',  # overridden by artus
		# ZJetCorrectionsProducer Settings
		'Jec': '', # path for JEC data, will be set later
		'L1Correction': 'L1FastJet',
		'RC': False,  # also provide random cone offset JEC, and use for type-I
		'FlavourCorrections': False,  # calculate additional MC flavour corrections
		# ZProducer Settings
		'ZMassRange': 20.,
		# TypeIMETProducer Settings
		'Met' : 'met', # metCHS will be selected automaticly if CHS jets are requested in TaggedJets
		'JetPtMin': 10.,
		'EnableMetPhiCorrection': False,
		'MetPhiCorrectionParameters': [],
		# Valid Jet Selection
		'ValidJetsInput': 'uncorrected',
		'JetID' : 'tight',
		'JetIDVersion' : 2014,
		'JetMetadata' : 'jetMetadata',
		'TaggedJets' : 'AK5PFTaggedJetsCHS',
		#PU
		'PileupDensity' : 'KT6Area',
		# Pipelines
		'Pipelines': {
			'default': {
				'CorrectionLevel': 'L1L2L3',
				'Consumers': [
					'ZJetLambdaNtupleConsumer',
					'cutflow_histogram',
				],
				'EventWeight': 'eventWeight',
				'Processors': [
					'filter:MuonPtCut',
					'filter:MuonEtaCut',
					'filter:LeadingJetPtCut',
					'filter:LeadingJetEtaCut',
					'filter:ZPtCut',
					'filter:BackToBackCut',
				],
				'Quantities': [
					# General quantities
					'npv', 'rho', 'weight', #'nputruth',
					'njets', 'njetsinv',  # number of valid and invalid jets
					# Z quantities
					'zpt', 'zeta', 'zy', 'zphi', 'zmass',
					# Leading jet
					'jet1pt', 'jet1eta', 'jet1y', 'jet1phi',
					'jet1chf', 'jet1nhf',
					'jet1mf', 'jet1hfhf', 'jet1hfemf', 'jet1pf',
					#'jet1unc',  # Leading jet uncertainty
					# Second jet
					'jet2pt', 'jet2eta', 'jet2phi',
					# MET and related
					'mpf', 'rawmpf', 'metpt', 'metphi', 'rawmetpt', 'rawmetphi', 'sumet',
				],
			},
		},

		# Wire Kappa objects
		'EventMetadata' : 'eventInfo',
		'LumiMetadata' : 'lumiInfo',
		'VertexSummary': 'goodOfflinePrimaryVerticesSummary',
	}
	return cfg

##
##


def data(cfg, **kwargs):
	cfg['InputIsData'] = True
	cfg['Pipelines']['default']['Quantities'] += ['run', 'event', 'lumi']
	cfg['Processors'] += [
		'filter:JsonFilter',
		'producer:HltProducer',
		'filter:HltFilter',
	]


def mc(cfg, **kwargs):
	cfg['InputIsData'] = False
	# put the gen_producer first since e.g. l5_producer depend on it

##
##


def _2011(cfg, **kwargs):
	cfg['Year'] = 2011


def _2012(cfg, **kwargs):
	cfg['Year'] = 2012


##
##


def ee(cfg, **kwargs):
	pass

def em(cfg, **kwargs):
	pass

def mm(cfg, **kwargs):
	cfg['Muons'] = 'muons'
	# The order of these producers is important!
	cfg['Processors'] = [
		'producer:ValidMuonsProducer',
		'filter:ValidMuonsFilter',
		#'producer:MuonCorrectionsProducer', # Is not doing anything yet
		'producer:ValidTaggedJetsProducer',
		'filter:ValidJetsFilter',
		'producer:ZJetCorrectionsProducer',
		'producer:TypeIMETProducer',
		'producer:JetSorter',
		'producer:ZProducer',
		'filter:ZFilter',
	]
	
	# ValidMuonsProducer
	cfg['MuonID'] = 'tight'
	cfg['MuonIso'] = 'tight'
	cfg['MuonIsoType'] = 'pf'
	cfg['DirectIso'] = True

	cfg['Pipelines']['default']['Quantities'] += [
		'mupluspt', 'mupluseta', 'muplusphi', 'muplusiso',
		'muminuspt', 'muminuseta', 'muminusphi', 'muminusiso',
		'mu1pt', 'mu1eta', 'mu1phi',
		'mu2pt', 'mu2eta', 'mu2phi',
		'nmuons',
	]

	cfg['CutMuonPtMin'] = 20.0
	cfg['CutMuonEtaMax'] = 2.3
	cfg['CutLeadingJetPtMin'] = 20.0
	cfg['CutLeadingJetEtaMax'] = 1.3
	cfg['CutZPtMin'] = 30.0
	cfg['CutBackToBack'] = 0.34


###
###


def data_2011(cfg, **kwargs):
	pass

def data_2012(cfg, **kwargs):
	cfg['Jec'] = ZJetConfigBase.getPath() + '/data/jec/Winter14_V6/Winter14_V5_DATA'
	cfg['JsonFiles'] = [ZJetConfigBase.getPath() + '/data/json/Cert_190456-208686_8TeV_22Jan2013ReReco_Collisions12_JSON.txt']
	cfg['MetPhiCorrectionParameters'] = [0.2661, 0.3217, -0.2251, -0.1747]

def mc_2011(cfg, **kwargs):
	pass

def mc_2012(cfg, **kwargs):
	cfg['Jec'] = ZJetConfigBase.getPath() + '/data/jec/Winter14_V6/Winter14_V5_MC'
	cfg['MetPhiCorrectionParameters'] = [0.1166, 0.0200, 0.2764, -0.1280]


def mcee(cfg, **kwargs):
	pass


def _2011mm(cfg, **kwargs):
	pass

def _2012mm(cfg, **kwargs):
	pass


##
##

def mc_2011mm(cfg, **kwargs):
	pass


def mc_2012ee(cfg, **kwargs):
	pass


def mc_2012mm(cfg, **kwargs):
	pass


def data_2011mm(cfg, **kwargs):
	pass


def data_2012mm(cfg, **kwargs):
	cfg['HltPaths'] = ['HLT_Mu17_Mu8_v%d' % v for v in range(1, 30)]


def data_2012ee(cfg, **kwargs):
	pass


def data_2012em(cfg, **kwargs):
	pass
