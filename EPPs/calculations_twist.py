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

class CalculationsTwist:
    def __init__(self, process):
        self.process = process
        self.iom = process.input_output_maps
        self.artifacts = []
        self.okej = 0
        self.failed = 0
        self.missing_udfs = []
        self.low_conc = 0

    def get_artifacts(self, process_type):
        if process_type== 'libval':
            self.artifacts = [io[1]['uri'] for io in self.iom if io[1]['output-generation-type'] == 'PerInput']
        else:
            all_artifacts = self.process.all_outputs(unique=True)
            self.artifacts = filter(lambda a: a.output_type == "Analyte" , all_artifacts)

    def calculate_volumes_for_aliquot(self):
        for art in self.artifacts:
            concentration = art.udf.get('Concentration')
            amount = art.udf.get('Amount (ng)')
            if not amount or not concentration:
                self.failed +=1
                self.missing_udfs += ['Amount (ng)', 'Concentration']
                art.qc_flag = 'FAILED'
                art.put()
                continue
            if amount >=250: 
                amount_needed=250
            elif 250> amount >=50: 
                amount_needed=50 
            elif 50> amount >=10:
                amount_needed=10
            else:
                amount_needed=amount
            art.qc_flag = 'PASSED'
            art.udf['Amount needed (ng)'] = amount_needed
            art.udf['Sample Volume (ul)'] = amount_needed/float(concentration)
            art.udf['Volume H2O (ul)'] = 30 - art.udf['Sample Volume (ul)']
            art.put()
            self.okej +=1
            

    def calcualate_amount_for_libval(self):
        sample_volume = self.process.udf.get('Sample Volume (ul)')
        amount_needed = self.process.udf.get('Amount Needed (ng)')
        for art in self.artifacts:
            concentration = art.udf.get('Concentration')
            if concentration == None:
                self.failed +=1
                self.missing_udfs += ['Concentration']
                continue
            art.udf['Amount (ng)'] = concentration*sample_volume
            if art.udf['Amount (ng)'] < amount_needed:
                art.qc_flag = 'FAILED'
            else:
                art.qc_flag = 'PASSED'
            art.put()
            self.okej +=1

def main(lims,args):
    process = Process(lims, id = args.pid)
    AT = CalculationsTwist(process)
    AT.get_artifacts(args.calculate)
    elif args.calculate == 'libval':
        AT.calcualate_amount_for_libval()
    elif args.calculate == 'aliquot':
        AT.calculate_volumes_for_aliquot()
    else:
        sys.exit('Non valid argument given. -c can take pooling/libval/aliquot')
    
    if AT.failed:
        missing = ', '.join( list(set(AT.missing_udfs)))
        abstract = 'Failed to perform calculations for '+ str(AT.failed)+ ' samples. Some of the following udfs are invalid or missing: ' +   missing + '. '
        sys.exit(abstract)
    if AT.okej:
        abstract = 'Performed calculations for '+ str(AT.okej)+ ' samples.'
        print >> sys.stderr, abstract


if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('-p', dest = 'pid',
                        help='Lims id for current Process')
    parser.add_argument("-c", dest='calculate', help = 'libval/aliquot')
    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()

    main(lims, args)
