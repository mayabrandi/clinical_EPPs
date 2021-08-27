#!/usr/bin/env python
DESC="""EPP script to performe calculations for pools in the twist WF


Maya Brandi


Science for Life Laboratory, Stockholm, Sweden
""" 
from argparse import ArgumentParser
from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD
from genologics.entities import Process
import sys

class Pool:
    def __init__(self, pool):
        pool.qc_flag='PASSED'
        self.total_volume = 0
        self.total_reads = 0
        self.pool = pool
        self.amount_fail = False
        self.pool_size = pool.udf.get('Total Amount (ng)')
        self.artifacts = pool.input_artifact_list()

    def get_total_reads(self):
        """Get the total numer of missing reads in the pool"""

        for art in self.artifacts:
            reads = art.samples[0].udf.get('Reads missing (M)')
            concentration = art.udf.get('Concentration')
            if reads is None or concentration is None:
                sys.exit('Missing udfs: Reads missing (M) or Concentration')
            self.total_reads += reads
        if self.total_reads == 0:
            sys.exit('All samples seem to have Missing Reads = 0. You dont want to sequence any of the samples?')

    def calculate_amount_and_volume(self):
        """Perform calcualtions for the input artifacts to the pool"""

        for art in self.artifacts:
            reads = art.samples[0].udf.get('Reads missing (M)')
            concentration = art.udf.get('Concentration')
            fract_of_pool = reads/float(self.total_reads)
            amount_to_pool = self.pool_size * fract_of_pool
            vol = amount_to_pool/concentration
            if amount_to_pool > art.udf.get('Amount (ng)') or amount_to_pool < 187.5:
                self.pool.qc_flag='FAILED'
                self.amount_fail = True
            art.udf['Amount taken (ng)'] = amount_to_pool
            art.udf['Volume of sample (ul)'] = vol
            art.put()
            self.total_volume += vol


class CalculationsForPools:
    def __init__(self, process, pools):
        self.pools = pools
        self.okej = 0
        self.failed = 0
        self.all_volumes= []
        self.amount_fail = False

    def calculate_volumes_for_pooling(self):
        """Perform calculations for each pool in the step"""

        for pool_art in self.pools:
            pool = Pool(pool_art)
            pool.get_total_reads()
            pool.calculate_amount_and_volume()
            if pool.amount_fail:
                self.amount_fail = True
            if pool.total_volume:
                pool_art.udf['Total Volume (ul)'] = pool.total_volume
                self.all_volumes.append(pool.total_volume)
                self.okej +=1
            else:
                self.failed +=1

    def calculate_volume_wather(self):
        """Perform wather calculations for each pool in the step"""

        for pool_art in self.pools:
            if pool_art.udf.get('Total Volume (ul)'):
                pool_art.udf['Volume H2O (ul)'] = max(self.all_volumes) - pool_art.udf.get('Total Volume (ul)')
            pool_art.put()
            

def main(lims,args):
    process = Process(lims, id = args.pid)
    pools = filter(lambda a: a.output_type == "Analyte" , process.all_outputs(unique=True))
    CFP = CalculationsForPools(process, pools)
    CFP.calculate_volumes_for_pooling()
    CFP.calculate_volume_wather()

 
    abstract = ''
    if CFP.amount_fail:
        abstract += 'Input amount low for samples in pool. Generate placement map for more info. '
    if CFP.failed:
        missing = ', '.join( list(set(CFP.missing_udfs)))
        abstract += 'Failed to perform calculations for '+ str(CFP.failed)+ ' pools. Some of the following udfs are invalid or missing: ' +   missing + '. '
    if CFP.okej:
        abstract += 'Performed calculations for '+ str(CFP.okej)+ ' pools.'

    if CFP.failed or CFP.amount_fail:
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
