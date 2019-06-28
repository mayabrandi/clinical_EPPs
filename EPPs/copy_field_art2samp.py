#!/usr/bin/env python
from __future__ import division
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process
from genologics.epp import EppLogger

import sys


DESC = """
"""


class CopyUDF():
    def __init__(self, process, samp_udf, art_udf):
        self.process = process
        self.artifacts = [a for a in process.all_outputs() if a.type=='Analyte']
        self.samp_udf = samp_udf
        self.art_udf = art_udf
        self.failed_udfs = False

    def copy(self):
        for art in self.artifacts:
            sample = art.samples[0]
            udf = art.udf.get(self.art_udf)
            if udf is not None:
                sample.udf[self.samp_udf] = udf
                sample.put()
            else:
                self.failed_udfs = True

def main(lims, args):
    process = Process(lims, id = args.pid)
    CUDF = CopyUDF(process, args.samp_udf, args.art_udf)
    CUDF.copy()

    if CUDF.failed_udfs:
        sys.exit('failed to copy some udfs')
    else:
        print >> sys.stderr, 'UDFs were succsessfully copied!'


if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('-p', dest = 'pid',
                        help='Lims id for current Process')
    parser.add_argument('-s', dest = 'samp_udf', help=(''))
    parser.add_argument('-a', dest = 'art_udf',
                        help=(''))
    args = parser.parse_args()
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    main(lims, args)
