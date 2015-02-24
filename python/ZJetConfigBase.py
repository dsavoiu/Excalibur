#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ArtusConfigBase provides the tools to make a valid artus config.

The most used functions are:
  - BaseConfig to generate a default configuration
  - CreateFileList to create a list of input files
  - Run to acutally call artus and run it
"""
import copy
import glob
import socket
import ConfigParser
import os
import stat
import getpass
import json
import sys
import ZJetConfigFunctions


def getConfig(inputtype, year, channel, **kwargs):
    """
        Main function to get a basic config.

        According to the three main categories (type, year, channel), the config
        is modified according to whats specified in ZJetConfigFunctions.
        All combinations of the categories are considered, if config functions are available.
    """

    # python class/function names cant start with a number -> add '_' to year
    l = [channel, inputtype, '_' + str(year)]
    print "Getting cfg for", channel, inputtype, year
    cfg = ZJetConfigFunctions.getBaseConfig(**kwargs)

    # iterate over all combinations and call updateConfig(single-entry tuples first):
    for i in l:
        updateConfig(cfg, (i), **kwargs)
    for i in l:
        for j in l:
            updateConfig(cfg, (i, j), **kwargs)
    for i in l:
        for j in l:
            for k in l:
                updateConfig(cfg, (i, j, k), **kwargs)

    return cfg


def updateConfig(conf, tupl, **kwargs):
    string = "".join(tupl)
    if string in dir(ZJetConfigFunctions):
        getattr(ZJetConfigFunctions, string)(conf, **kwargs)


def setInputFiles(ekppath, nafpath=None):
    """Return ekppath if you're at EKP, nafpath if at NAF. """
    d = {'ekp': ekppath, 'naf': nafpath}
    host = socket.gethostname()[:3]
    if host in d:
        if d[host] in [None, '']:
            sys.exit("ERROR: You're at %s, but the path for this skim is not set here!" % host.upper())
        else:
            return d[host]
    else:
        sys.exit("ERROR: Cant determine input file location!")


def expand(config, variations=[], algorithms=[], default="default"):
    """create pipelines for each algorithm times each variation"""
    pipelines = config['Pipelines']
    p = config['Pipelines'][default]
    if p['JetAlgorithm'] not in algorithms:
        algorithms.append(p['JetAlgorithm'])
    if config['InputType'] == 'data' and "Res" not in p['JetAlgorithm']:
        algorithms.append(p['JetAlgorithm'] + "Res")

    #find global algorithms
    config["GlobalAlgorithms"] = []
    removelist = ["Jets", "L1", "L2", "L3", "Res", "Hcal", "Custom"]
    for algo in algorithms:
        for r in removelist:
            algo = algo.replace(r, "").replace("CHS", "chs")
        if algo not in config["GlobalAlgorithms"]:
            config["GlobalAlgorithms"].append(algo)

    # copy for variations
    for v in variations:
        if v == 'nocuts':
            pipelines[v] = copy.deepcopy(p)
            pipelines[v]['Cuts'] = []
            if 'finalcuts' in pipelines[v]['Filter']:
                    pipelines[v]['Filter'].remove('finalcuts')
        elif v == 'zcuts':
            pipelines[v] = copy.deepcopy(p)
            removelist = ['leadingjet_pt', 'back_to_back']
            for cut in removelist:
                if cut in pipelines[v]['Cuts']:
                    pipelines[v]['Cuts'].remove(cut)
        elif v == 'fullcuts':
            pipelines[v] = copy.deepcopy(p)
            pipelines[v]['Cuts'].append('leadingjet_eta')
            pipelines[v]['Cuts'].append('secondleading_to_zpt')
            pipelines[v]['CutLeadingJetEta'] = 1.3
            pipelines[v]['CutSecondLeadingToZPt'] = 0.2
        elif v == 'finalcuts':
            pipelines[v] = copy.deepcopy(p)

    # remove template pipeline
    pipelines.pop(default)

    # copy for algorithms, naming scheme: incut_algo
    for name, p in pipelines.items():
        for algo in algorithms:
            pipelines[name + "_" + algo] = copy.deepcopy(p)
            pipelines[name + "_" + algo]["JetAlgorithm"] = algo
        del pipelines[name]

    return config


def pipelinediff(config, to=None):
    print "Comparing", len(config['Pipelines']), "pipelines:"
    if to == None:
        to = filter(lambda x: 'finalcuts' in x, config['Pipelines'].keys())[0]

    for name, p in config['Pipelines'].items():
        if name != to:
            print "- Compare", name, "to", to
            pipelinediff2(p, config['Pipelines'][to])
    print


def pipelinediff2(p1=None, p2=None):
    for k, v in p1.items():
        if k in p2.keys():
            if p1[k] != p2[k]:
                print "    different %s: %s != %s" % (k, str(p1[k]), str(p2[k]))

