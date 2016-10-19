#!/usr/bin/env python
from __future__ import division
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process
from genologics.epp import EppLogger

import logging
import sys

DESC = """epp script to calculate EB Volume from Concentration udf

Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""


class EBVol():

    def __init__(self, process, aggregate):
        self.process = process
        self.aggregate = aggregate
        self.artifacts = []
        self.passed_arts = []
        self.failed_arts = []
        self.final_vol = 5.0

    def get_artifacts(self):
        if self.aggregate:
            self.artifacts = self.process.all_inputs(unique=True)
        else:
            all_artifacts = self.process.all_outputs(unique=True)
            self.artifacts = filter(lambda a: a.output_type == "Analyte" , all_artifacts)


    def apply_calculations(self):
        for art in self.artifacts:
            udfs_ok = True
            try:
                int(art.udf['Concentration (nM)'])
            except:
                udfs_ok = False
            try:
                int(art.udf['Final Concentration (nM)'])
            except:
                udfs_ok = False
            if udfs_ok:
                art.udf['Volume of sample (ul)'] = art.udf['Final Concentration (nM)']*self.final_vol/art.udf['Concentration (nM)']
                art.udf['Volume of RSB (ul)'] = self.final_vol-art.udf['Volume of sample (ul)']
                art.put()
                self.passed_arts.append(art)
            else:
                self.failed_arts.append(art)            



def main(lims, args):
    process = Process(lims, id = args.pid)
    EBV = EBVol(process, args.aggregate)
    EBV.get_artifacts()
    EBV.apply_calculations()


    d = {'ca': len(EBV.passed_arts),
         'ia': len(EBV.failed_arts)}
    abstract = ("Updated {ca} artifact(s), skipped {ia} artifact(s) with "
                "wrong and/or blank values for some udfs.").format(**d)

    print >> sys.stderr, abstract 

if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid',
                        help='Lims id for current Process')
    parser.add_argument('--log', default=sys.stdout,
                        help=('File name for standard log file, '
                              'for runtime information and problems.'))
    parser.add_argument('--aggregate', action='store_true',
                        help=("Use this tag if your process is aggregating "
                              "results. The default behaviour assumes it is "
                              "the output artifact of type analyte that is "
                              "modified while this tag changes this to using "
                              "input artifacts instead"))

    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    with EppLogger(args.log, lims=lims, prepend=True) as epp_logger:
        main(lims, args)
