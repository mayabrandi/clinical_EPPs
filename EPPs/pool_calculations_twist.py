#!/usr/bin/env python
DESC="""EPP script to performe calculations in some different steps in the twist WF


Maya Brandi


Science for Life Laboratory, Stockholm, Sweden
""" 
from argparse import ArgumentParser
from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD
from genologics.entities import Process
import sys

class Pool(self):
    def __init__(self, pool):
        self.qc_flag='PASSED'
        self.total_volume = 0
        self.total_reads = 0
        self.pool_size = pool.udf.get('Total Amount (ng)')
        self.artifacts = pool.input_artifact_list()


    def get_total_reads(self):
        for art in self.artifacts:
            reads = art.samples[0].udf.get('Reads missing (M)')
            concentration = art.udf.get('Concentration')
            if reads is None or concentration is None:
                sys.exit('Missing udfs: Reads missing (M) or Concentration')
            self.total_reads += reads
        if self.total_reads == 0:
            sys.exit('All samples seem to have Missing Reads = 0. You dont want to sequence any of the samples?')

    def calculate_amount_and_volume(self):
        for art in artifacts:
            reads = art.samples[0].udf.get('Reads missing (M)')
            concentration = art.udf.get('Concentration')
            fract_of_pool = reads/float(self.total_reads)
            amount_to_pool = self.pool_size * fract_of_pool
            vol = amount_to_pool/concentration
            if amount_to_pool > art.udf.get('Amount (ng)'):
                pool.qc_flag='FAILED'
                self.amount_fail = True
            art.udf['Amount taken (ng)'] = amount_to_pool
            art.udf['Volume of sample (ul)'] = vol
            art.put()
            self.total_volume += vol


class CalculationsTwist:
    def __init__(self, process):
        self.process = process
        self.iom = process.input_output_maps
        self.artifacts = []
        self.amount_fail = False
        self.okej = 0
        self.failed = 0
        self.missing_udfs = []
        self.low_conc = 0
        self.all_volumes= []

    def get_artifacts(self, process_type):
        all_artifacts = self.process.all_outputs(unique=True)
        self.artifacts = filter(lambda a: a.output_type == "Analyte" , all_artifacts)

    def calculate_volumes_for_pooling(self):
        for pool_art in self.artifacts:
            pool = Pool(art)
            pool.get_total_reads()
            pool.calculate_amount_and_volume()
            if pool.total_volume:
                pool_art.udf['Total Volume (ul)'] = pool.total_volume
                self.all_volumes.append(pool.total_volume)
                self.okej +=1
            else:
                self.failed +=1

    def calculate_volume_wather(self):
        for pool in self.artifacts:
            pool.udf['Volume H2O (ul)'] = max(self.all_volumes) - pool.udf.get('Total Volume (ul)')
            pool.put()
            

def main(lims,args):
    process = Process(lims, id = args.pid)
    AT = CalculationsTwist(process)
    AT.get_artifacts(args.calculate)
    AT.calculate_volumes_for_pooling()
    AT.calculate_volume_wather() 
    abstract = ''
    if AT.amount_fail:
        abstract += 'Input amount low for samples in pool. Generate placement map for more info. '
    if AT.failed:
        missing = ', '.join( list(set(AT.missing_udfs)))
        abstract += 'Failed to perform calculations for '+ str(AT.failed)+ ' samples. Some of the following udfs are invalid or missing: ' +   missing + '. '
    if AT.okej:
        abstract += 'Performed calculations for '+ str(AT.okej)+ ' samples.'

    if AT.failed or AT.amount_fail:
        sys.exit(abstract)
    else:
        print >> sys.stderr, abstract

if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('-p', dest = 'pid',
                        help='Lims id for current Process')
    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()

    main(lims, args)
