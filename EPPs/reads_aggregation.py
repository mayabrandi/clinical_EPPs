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

class SumReadsRML():
    def __init__(self, pools):
        self.pools = pools
        self.passed_pool_replicates = {}

    def get_pool_replicates(self, pool):
        """Given any submitted sample ("pool_representative") that is part of the pool we are looking for,
           return all replicates (lanes and/ore reruns) of the pool thats been run throuh sequencing.

        The function assumes a submitted sample will occure in only one pool

                                        <-- pool_replicate_11
        submitted sample_X <--> pool_1  <-- pool_replicate_12
                                        <-- pool_replicate_13

                                        <-- pool_replicate_21
        submitted sample_Y <--> pool_2  <-- pool_replicate_22
                                        <-- pool_replicate_23
        ..."""


        #first sample in the pool
        pool_representative = pool.samples[0]
        #all outputs from sequencing where pool_representative was part
        out_arts = lims.get_artifacts(samplelimsid = pool_representative.id,
                   process_type = ["CG002 - Illumina Sequencing (Illumina SBS)"])
        out_arts = list(set(out_arts))

        #all inputs to all sequecing processes where pool_representative was part
        inputs = []
        for a in out_arts:
            inputs += a.parent_process.all_inputs()
        inputs = list(set(inputs))

        #get pool replicates
        pool_replicates = []
        pool.samples.sort()
        for inp in inputs:
            inp.samples.sort()
            if set(pool.samples) < set(inp.samples): ## if pool.samples is subset of inp.samples
                pool_replicates.append(inp)
        return pool_replicates


    def sum_reads(self, pool_replicates):
        """Sum passed reads from all pool_replicates. Set 'Total Reads (M)' for each samp in the pool. 
        Will be the same for all samples in the pool."""
        total_reads = 0.0
        pool_name = pool_replicates[0].name
        nr_lanes = 0
        for pool in pool_replicates:
            if pool.qc_flag == 'PASSED' and 'Clusters PF R1' in pool.udf:
                total_reads += float(pool.udf.get('Clusters PF R1'))
                nr_lanes +=1
        M_reads = total_reads/1000000
        for s in pool_replicates[0].samples:
            s.udf['Total Reads (M)'] =  M_reads
            s.put()
        return nr_lanes


    def set_udfs(self):
        """Set Total Reads on all samps"""
        for pool in self.pools:
            pool_replicates = self.get_pool_replicates(pool)
            nr_lanes = self.sum_reads(pool_replicates)
            self.passed_pool_replicates[pool.name]=nr_lanes


class SumReads():
    def __init__(self, samples):
        self.samples = samples
        self.failed_samps = 0
        self.passed_samps =0

    def sum_reads(self, sample):
        """Sum passed sample reads from all lanes and runs. Return total reads in Milions"""
        total_reads = 0.0
        arts = lims.get_artifacts(samplelimsid = sample.id,
               process_type = ["CG002 - Bcl Conversion & Demultiplexing (Illumina SBS)"])
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

class PoolsAndSamples():
    def __init__(self, process):
        self.process = process
        self.samples = []
        self.pools = []

    def get_pools_and_samples(self):
        all_artifacts = self.process.all_inputs(unique=True)
        samples = []
        for a in all_artifacts:
            if len(a.samples) > 1:
                self.pools.append(a)
            elif len(a.samples) == 1:
                samples += a.samples
        self.samples = list(set(samples))


def main(lims, args):
    process = Process(lims, id = args.pid)
    PAS = PoolsAndSamples(process)
    PAS.get_pools_and_samples()
    if PAS.samples:
        abstract = 'Found Samples - Summing demultiplexed reads on sample level. '
        SR = SumReads(PAS.samples)
        SR.set_udfs()
        abstract += "Reads aggregated for "+str(SR.passed_samps)+" sample(s)."
    if PAS.pools:
        abstract = 'Found pools - Summing clusters on lane level. '
        SRRML = SumReadsRML(PAS.pools)
        SRRML.set_udfs()
        abstract += "Reads summed for: "
        for k, v in SRRML.passed_pool_replicates.items():
            abstract += str(k) +' from '+str(v)+' lanes, '

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
