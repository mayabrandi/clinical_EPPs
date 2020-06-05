#!/usr/bin/env python
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process
import sys

DESC = """EPP script to check amount needed on output artifacts

Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""

def check_amounts(process):
    out_analytes = [a for a in process.all_outputs() if a.type=='Analyte']
    for art in out_analytes:
        amount = art.udf.get('Amount needed (ng)')
        if amount not in [50, 250, 10] and amount >10:
            sys.exit('Amount needed (ng) must be within [50, 250, <10]')

def main(lims, args):
    process = Process(lims, id = args.p)
    check_amounts(process)

if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('-p', help='Lims id for current Process')

    args = parser.parse_args()
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    main(lims, args)
