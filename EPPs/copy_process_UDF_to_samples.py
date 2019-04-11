#!/usr/bin/env python
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process
import sys

DESC = """Script to copy udf from process to samples

Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""


class CopyUDF():

    def __init__(self, process):
        self.process = process
        self.date = self._get_date()
        self.samples = []

    def _get_date(self):
        date = self.process.udf.get('Date delivered')
        if not date:
            sys.exit('Date delivered is not set.')
        return date

    def get_samples(self):
        all_artifacts = self.process.all_inputs()
        for art in all_artifacts: 
            self.samples += art.samples
        self.samples = set(self.samples)

    def set_date(self):
        for sample in self.samples:
            sample.udf['Delivered'] = self.date
            sample.put()

def main(args):
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()

    process = Process(lims, id = args.pid)

    CUDF = CopyUDF(process)
    CUDF.get_samples()
    CUDF.set_date()


if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid',
                        help='Lims id for current Process')
    args = parser.parse_args()
    main(args)
