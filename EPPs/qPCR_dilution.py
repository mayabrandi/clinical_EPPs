#!/usr/bin/env python
from __future__ import division
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process
from genologics.epp import EppLogger

from openpyxl import load_workbook
import json
from statistics import mean
from clinical_EPPs import WELL_TRANSFORMER


import logging
import sys

DESC = """epp script to ...
    dilution_file   - qPCR Result file. Uploded by user.

Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""


class QpcrDilution():

    def __init__(self, process):
        self.process = process
        self.artifacts = {}
        self.passed_arts = 0
        self.failed_arts = 0
        self.dilution_data = {}
        self.molar = {}
        self.bla = {}


    def make_dilution_data(self, dilution_file):
        dilution_file = self.get_file()
        wb=load_workbook(dilution_file)
        ws = wb.active
        for row in ws.iter_rows():
            well = row[1].value
            Cq = row[6].value
            SQ = row[7].value
            if type(Cq)==float and type(SQ) == float:
                orwell = WELL_TRANSFORMER[well]['well']
                dilut = WELL_TRANSFORMER[well]['dilut']
                if dilut in ['1E03','2E03','1E04']:
                    if not orwell in self.dilution_data.keys():
                        self.dilution_data[orwell] = {
                            'SQ' : {'1E03':[],'2E03':[],'1E04':[]},
                            'Cq' : {'1E03':[],'2E03':[],'1E04':[]}}
                    self.dilution_data[orwell]['SQ'][dilut].append(SQ)
                    self.dilution_data[orwell]['Cq'][dilut].append(Cq)

    def calculate_molar(self, artifact):
        size_bp = 470 # standard size bp used is: 470
        inart = artifact['in']
        outart = artifact['out']
        well = inart.location[1]
        SQ_1E03 = mean(self.dilution_data[well]['SQ']['1E03'])
        SQ_2E03 = mean(self.dilution_data[well]['SQ']['2E03'])
        SQ_1E04 = mean(self.dilution_data[well]['SQ']['1E04'])
        orig_conc = (SQ_1E03*1000+SQ_2E03*2000+SQ_1E04*10000)/3
        size_adjust_conc_M = orig_conc*(452/size_bp)
        size_adjust_conc_nM= size_adjust_conc_M*1000000000
        Cq_1E03 = mean(self.dilution_data[well]['Cq']['1E03'])
        Cq_2E03 = mean(self.dilution_data[well]['Cq']['2E03'])
        Cq_1E04 = mean(self.dilution_data[well]['Cq']['1E04'])


        try:
            outart.udf['Concentration'] = size_adjust_conc_M
            outart.udf['Size (bp)'] = int(size_bp)
            outart.udf['Concentration (nM)'] = size_adjust_conc_nM
            if outart.udf['Concentration (nM)'] < 2:
                outart.qc_flag = "FAILED"
            else:
                outart.qc_flag = "PASSED"
            outart.put()
            self.passed_arts +=1
        except:
            self.failed_arts +=1

    def set_udf(self):
        for samp_id, art in self.artifacts.items():
            self.calculate_molar(art)

    def get_artifacts(self):
        in_arts = self.process.all_inputs(unique=True)
        all_artifacts = self.process.all_outputs(unique=True)
        out_artifacts = filter(lambda a: a.output_type == "ResultFile" , all_artifacts)
        for a in in_arts:
            samp = a.samples[0].id
            self.artifacts[samp] = {'in': a}
        for a in out_artifacts:
            samp = a.samples[0].id
            self.artifacts[samp]['out'] = a

    def get_file(self):
        for f in self.process.shared_result_files():
            if f.name =='qPCR Result File':
                qPCR_file = f.files[0]
        return qPCR_file.content_location.split('scilifelab.se')[1]


def main(lims, args):
    process = Process(lims, id = args.pid)
    QD = QpcrDilution(process)
    QD.get_artifacts()
    QD.make_dilution_data(args.dil_file)
    QD.set_udf()

    d = {'ca': QD.passed_arts,
         'ia': QD.failed_arts}
    abstract = ("Updated {ca} artifact(s), skipped {ia} artifact(s) with "
                "wrong and/or blank values for some udfs.").format(**d)

    if QD.failed_arts:
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
    parser.add_argument('--dil_file', default=None,
                       help=('File name for qPCR result file.'))

    args = parser.parse_args()
    if not args.dil_file:
        sys.exit('Dilution File missing!')

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args)

