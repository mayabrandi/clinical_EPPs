#!/usr/bin/env python
from __future__ import division
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process, ReagentType
from genologics.epp import EppLogger

import logging
import sys

DESC = """epp script to check for duplicate indexes in pools 

Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""

class Pool():
    def __init__(self, pool):
        self.pool = pool
        self.pooled_arts =  pool.input_artifact_list()
        self.index_dict = {}
        self.duplicates = []

    def check_index(self):
        for art in self.pooled_arts:
            reagent_label_names = art.reagent_labels
            for name in reagent_label_names:
                reagent_types = lims.get_reagent_types(name=name)
                if len(reagent_types)==1: #(Will never be morte than one. names are unique)
                    sequence = reagent_types[0].sequence
                    if sequence in self.index_dict.keys():
                        self.index_dict[sequence][art] = name
                        self.duplicates.append(sequence)
                    else:
                        self.index_dict[sequence] = {art : name}

class CheckIndex():

    def __init__(self, process):
        self.process = process
        self.pools = []
        self.abstract = []

    def get_artifacts(self):
        all_artifacts = self.process.all_outputs()
        self.pools = filter(lambda a: a.output_type == "Analyte" , all_artifacts)

    def check_each_pool(self):
        for pool in self.pools:
            P = Pool(pool)
            P.check_index()
            if P.duplicates:
                self.add_to_abstract(P)

    def add_to_abstract(self, P):
        self.abstract.append('Duplicates in Pool: '+ P.pool.name)
        for index in P.duplicates:
            art_dict = P.index_dict[index]
            for art, index_name in art_dict.items():
                self.abstract.append(', '.join([art.name, index_name, index]))

def main(lims, args):
    process = Process(lims, id = args.pid)
    CI = CheckIndex(process)
    CI.get_artifacts()
    CI.check_each_pool()

    if CI.abstract:
        sys.exit(' '.join(CI.abstract))

if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid',
                        help='Lims id for current Process')
    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args)
