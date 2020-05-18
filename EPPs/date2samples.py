#!/usr/bin/env python
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process
import sys
from datetime import datetime as dt

DESC = """Script to copy udf from process to samples

Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""


class CopyUDF():

    def __init__(self, process, pudf, sudf, out):
        self.process = process
        self.pudf = pudf
        self.sudf = sudf
        self.out = out
        self.date = self._get_date()
        self.samples = []

    def _get_date(self):
        if self.pudf:
            date = self.process.udf.get(self.pudf)
        else:
            date = dt.today().date()
        if not date:
            sys.exit(self.pudf + ' is not set.')
        return date

    def get_artifacts(self):
        if self.out:
            self.artifacts = [a for a in self.process.all_outputs() if a.type=='Analyte']
        else:
            self.artifacts = self.process.all_inputs()        

    def get_samples(self):
        for art in self.artifacts: 
            if art.qc_flag=='FAILED':
                continue
            self.samples += art.samples
        self.samples = set(self.samples)

    def set_date(self):
        for sample in self.samples:
            sample.udf[self.sudf] = self.date
            sample.put()

def main(args):
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()

    process = Process(lims, id = args.pid)

    CUDF = CopyUDF(process, args.pudf, args.sudf, args.out)
    CUDF.get_artifacts()
    CUDF.get_samples()
    CUDF.set_date()


if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid',
                        help='Lims id for current Process')
    parser.add_argument('--sudf',
                        help='UDF on sample to set')
    parser.add_argument('--pudf',
                        help='UDF on process to fetch. If none, use date_run')
    parser.add_argument('--out', action='store_true',
                        help='check QC flags on output artifacts.')
    args = parser.parse_args()
    main(args)
