#!/usr/bin/env python
from __future__ import division
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process
import logging
import sys

DESC = """EPP script to calculate dilution volumes from Concentration udf

Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""


class CalculateDilution():

    def __init__(self, process):
        self.process = process
        self.out_analytes = [a for a in process.all_outputs() if a.type=='Analyte']
        self.passed_arts = []
        self.failed_arts = []
        self.final_vol = 25 
        self.final_vol_if_litle_sample = 50
        self.final_conc = 4 

    def apply_calculations(self):
        for art in self.out_analytes:
            udfs_ok = True
            try:
                int(art.udf['Concentration'])
            except Exception as e:
                logging.exception(e) 
                udfs_ok = False
            if udfs_ok:
                sample_vol = self.final_conc*self.final_vol/art.udf['Concentration']
                art.udf['Final Volume (uL)'] = self.final_vol
                if sample_vol < 0.5:
                    sample_vol = self.final_conc*self.final_vol_if_litle_sample/art.udf['Concentration']
                    art.udf['Final Volume (uL)'] = self.final_vol_if_litle_sample
                art.udf['Volume H2O (ul)'] =  art.udf['Final Volume (uL)'] - sample_vol
                art.udf['Volume of sample (ul)'] = sample_vol 
                art.put()
                self.passed_arts.append(art)
            else:
                self.failed_arts.append(art)            



def main(lims, args):
    process = Process(lims, id = args.p)
    CD = CalculateDilution(process)
    CD.apply_calculations()


    d = {'ca': len(CD.passed_arts),
         'ia': len(CD.failed_arts)}
    abstract = ("Updated {ca} artifact(s), skipped {ia} artifact(s) with "
                "wrong and/or blank values for some udfs.").format(**d)

    if CD.failed_arts:
        sys.exit(abstract)
    else:
        print >> sys.stderr, abstract 

if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('-p',
                        help='Lims id for current Process')
    parser.add_argument('-l', dest='log' , default=sys.stdout,
                        help=('File name for standard log file, '
                              'for runtime information and problems.'))

    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    logging.basicConfig(
                    level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename = args.log,
                    filemode='w')
    main(lims, args)
