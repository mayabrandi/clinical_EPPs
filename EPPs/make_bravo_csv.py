#!/home/glsai/miniconda2/envs/epp_master/bin/python
from __future__ import division
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process
from genologics.epp import EppLogger

import logging
import sys
import csv


DESC = """epp script to generate Bravo CSV file
Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""


class BravoCSV():

    def __init__(self, process, bravo_csv):
        self.csv = bravo_csv+'_bravo_nomalization.csv'
        self.process = process
        self.artifacts = []
        self.failed_arts = []

    def get_artifacts(self):
        all_artifacts = self.process.all_outputs(unique=True)
        self.artifacts = filter(lambda a: a.output_type == "Analyte" , all_artifacts)

    def make_csv(self):
        with open( self.csv , 'wb') as bravo_csv:
            wr = csv.writer(bravo_csv)
            art_dict = {a.location[1] : a  for a in self.artifacts}
            for row in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                for col in range(1,13):
                    well = row + ':' + str(col)
                    if well in art_dict:
                        art = art_dict[well]
                        try:
                            row_list = [row + str(col) , str(art.udf['Volume Buffer (ul)']), str(art.udf['Sample Volume (ul)'])]
                            wr.writerow(row_list)
                        except:
                            self.failed_arts.append(art.name)

def main(lims, args):
    process = Process(lims, id = args.pid)
    BCSV = BravoCSV(process, args.csv)
    BCSV.get_artifacts()
    BCSV.make_csv()


    d = {'ia': ', '.join(BCSV.failed_arts)}

    if BCSV.failed_arts:
        abstract = ("Wrong and/or blank values for some udfs. Could not add sample "
                 "information to Bravo CSV for the following samples: {ia}").format(**d)
        sys.exit(abstract)
    else:
        abstract = "Bravo CSV sucsessfully generated."
        print >> sys.stderr, abstract


if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid',
                        help='Lims id for current Process')
    parser.add_argument('--log', default=sys.stdout,
                        help=('File name for standard log file, '
                              'for runtime information and problems.'))
    parser.add_argument('--csv', default=sys.stdout,
                        help=('csv file'))

    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args)
