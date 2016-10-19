#!/usr/bin/env python
from __future__ import division
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process
from genologics.epp import EppLogger

import logging
import sys
import os


DESC = """
"""

class SumReads():
    def __init__(self, process):
        self.process = process
        self.samples = [] 
        self.passed_samps = 0
        self.failed_samps = 0
        
    def get_samples(self):
        """make unique sample list based on all in arts"""
        all_artifacts = self.process.all_inputs(unique=True)
        samples = []
        for a in all_artifacts:
            samples += a.samples
        self.samples = list(set(samples))
    
    def sum_reads(self, sample):
        """Sum passed sample reads from all lanes and runs. Return total reads in Milions"""
        total_reads = 0.0
        arts = lims.get_artifacts(samplelimsid = sample.id, 
               process_type = ["CG002 - Bcl Conversion & Demultiplexing (Illumina SBS) 4.0"]) 
        for art in arts:
            if art.qc_flag == 'PASSED' and '# Reads' in art.udf:
                total_reads += float(art.udf.get('# Reads'))
        return total_reads/1000000

    def set_udfs(self):
        """Set Total Reads on all samps"""
        for samp in self.samples:
            M_reads = self.sum_reads(samp)
            try:
                samp.udf['Total Reads (M)'] =  M_reads
                samp.put()
                self.passed_samps +=1
            except:
                self.failed_samps +=1
                pass


def main(lims, args):
    process = Process(lims, id = args.pid)
    SR = SumReads(process)
    SR.get_samples()
    SR.set_udfs()

    d = {'ca': SR.passed_samps,
        'wa' : SR.failed_samps}
    abstract = ("Reads aggregated for {ca} sample(s).").format(**d)

    if SR.failed_samps:
        sys.exit(abstract)
    else:
        print >> sys.stderr, abstract 

if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('-p', dest = 'pid',
                        help='Lims id for current Process')
    parser.add_argument('-l', dest = 'log', default=sys.stdout,
                        help=('File name for standard log file, '
                              'for runtime information and problems.'))

    args = parser.parse_args()
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args)
