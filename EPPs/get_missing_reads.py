#!/usr/bin/env python
from __future__ import division
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process
from genologics.epp import EppLogger
from lims.utils.core import parse_application_tag
import logging
import sys

DESC = """Epp script to calculate calculate Missing Reads, set the Rerun check box and set the Sequencing QC flag.

Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""


class MissingReads():

    def __init__(self, process):
        self.process = process
        self.artifacts = []
        self.passed_arts = []
        self.failed_arts = []

    def get_artifacts(self):
        all_artifacts = self.process.all_outputs(unique=True)
        self.artifacts = filter(lambda a: a.output_type == "Analyte" , all_artifacts)


    def get_missing_reads(self):
        for art in self.artifacts:
            sample = art.samples[0]
            udfs_ok = True
            try:
                reads_total = sample.udf['Total Reads (M)']
                app_tag = sample.udf['Sequencing Analysis']
            except:
                udfs_ok = False
            if udfs_ok:
                target_amount = parse_application_tag(app_tag)['reads']/1000000
                reads_min = 0.75*target_amount
                reads_missing = reads_min - reads_total
                if reads_missing > 0:
                    sample.udf['Reads missing (M)'] = target_amount
                    art.udf['Rerun'] = True
                    art.qc_flag = 'FAILED'
                else:
                    sample.udf['Reads missing (M)'] = 0
                    art.udf['Rerun'] = False
                    art.qc_flag = 'PASSED'
                art.put()
                sample.put()
                self.passed_arts.append(art)
            else:
                self.failed_arts.append(art)            

        

def main(lims, args):
    process = Process(lims, id = args.pid)
    MR = MissingReads(process)
    MR.get_artifacts()
    MR.get_missing_reads()


    d = {'ca': len(MR.passed_arts),
         'ia': len(MR.failed_arts)}
    abstract = ("Updated {ca} sample(s), skipped {ia} sample(s) with "
                "wrong and/or blank values for some udfs.").format(**d)

    print >> sys.stderr, abstract

if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('-p', dest = 'pid',
                        help='Lims id for current Process')
    parser.add_argument('-l', default=sys.stdout, dest = 'log',
                        help=('File name for standard log file, '
                              'for runtime information and problems.'))

    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args)
