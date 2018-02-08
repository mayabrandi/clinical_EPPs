#!/usr/bin/env python
from __future__ import division
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process
from genologics.epp import EppLogger

from openpyxl import load_workbook
import json
from statistics import mean, median
import numpy
from clinical_EPPs import WELL_TRANSFORMER
import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile


import logging
import sys

DESC = """epp script to ...
    dilution_file   - qPCR Result file. Uploded by user.

Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""


class File2UDF():

    def __init__(self, process, result_file, udfs, col_names):
        self.process = process
        self.artifacts = {}
        self.passed_arts = []
        self.failed_arts = []


    def get_artifacts(self):
        in_arts = self.process.all_inputs(unique=True)
        all_artifacts = self.process.all_outputs(unique=True)
        out_artifacts = filter(lambda a: a.output_type == "Analyte" , all_artifacts)
        for art in out_artifacts:
            well = art.location[0]
            self.artifacts[well] = art


    def set_udfs(self, dilution_file):
        """"""
        df = pd.read_excel(self.result_file)
        for i, row in df.iterrows():
            well = row['Well']
            art = self.artifacts[well]
            for ind, col_name in enumerate(self.col_names):
                try:
                    art.udfs[self.udfs] = row[col_name]
                    self.passed_arts.append(art.id)
                except:
                    self.failed_arts.append(art.id)





def main(lims, args):
    process = Process(lims, id = args.pid)
    F2UDF = File2UDF(process, args.result_file, args.udfs, args.col_names)
    F2UDF.get_artifacts()
    F2UDF.set_udfs()

    d = {'ca': QD.passed_arts,
         'ia': QD.failed_arts}
    abstract = ("Updated {ca} artifact(s), skipped {ia} artifact(s) with "
                "wrong and/or blank values for some udfs.").format(**d)
   
    if F2UDF.failed_arts:
        sys.exit(abstract)
    else:
        print >> sys.stderr, abstract

if __name__ == "__main__":
    # Initialize parser with standard arguments and description
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid',
                       help='Lims id for current Process')
    parser.add_argument('--log', default=sys.stdout,
                       help=('File name for standard log file, '
                              'for runtime information and problems.'))
    parser.add_argument('--result_file', default=None,
                       help=(''))

    parser.add_argument('--udfs', default=None,
                       help=(''))
    parser.add_argument('--col_names', default=None,
                       help=(''))


    args = parser.parse_args()
    if not args.dil_file:
        sys.exit('Dilution File missing!')
    if len(args.udfs)!=len(args.col_names):
        sys.exit('udfs to be set has to be of the same numer as col_names!')


    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args)
