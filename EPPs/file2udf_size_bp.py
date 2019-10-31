#!/usr/bin/env python
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD
from genologics.entities import Process, Artifact

from csv import DictReader
import sys
import os



DESC = """epp script to ...
    Reads a excel file with column names: Well, col_name 1, col_name 2, etc.

    On the artifact located in the well, sets the value from col_name 1 on udf 1, col_name on udf 2, etc. 
    Not in prod yet. 


Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""


class File2UDF():

    def __init__(self, lims, pid):
        self.lims = lims
        self.process = Process(lims, id = pid)
        self.input_output_maps = self.process.input_output_maps
        self.artifacts = {}
        self.failed_arts = False
        self.passed_arts = 0
        self.all_arts = 0
        self.result_file = None

    def get_artifacts(self):
        for inp, outp in self.input_output_maps:
            if outp.get("output-generation-type") == "PerAllInputs":
                continue
            in_art = Artifact(self.lims,id = inp['limsid'])
            out_art = Artifact(self.lims,id = outp['limsid'])
            col,row = in_art.location[1].split(':')
            well = col + row
            self.artifacts[well] = out_art
            self.all_arts += 1

    def get_result_file(self, result_file):
        if result_file and os.path.isfile(result_file):
            self.result_file = result_file
        else:
            files = filter(lambda a: a.name in ["Tapestation CSV"], self.process.all_outputs())
            if len(files)>1:
                sys.exit('more than one Qubit Result File')
            else:
                self.result_file = files[0].files[0].content_location.split('scilifelab.se')[1]

    def set_udfs(self):
        with open(self.result_file) as f:
            d = DictReader(f, delimiter=';')
            l = list(d)
        for sample in l:
            well = sample.get('WellId')
            size = sample.get('Average Size [bp]')
            if size and well in self.artifacts:
                art = self.artifacts[well]
                art.udf['Size (bp)'] = int(size)
                art.put()
                self.passed_arts += 1
            else:
                self.failed_arts = True



def main(lims, args):
    F2UDF = File2UDF(lims, args.pid)
    F2UDF.get_result_file(args.result_file)
    F2UDF.get_artifacts()
    F2UDF.set_udfs()
    

    abstract = "Updated %s out of %s artifact(s)." % (str(F2UDF.passed_arts), str(F2UDF.all_arts))
    if F2UDF.failed_arts:
        abstract += ' Some of the samples in the csv file are not represented as samples in the step.'
    if F2UDF.passed_arts < F2UDF.all_arts:
        abstract += ' Some samples in the step were not represented in the file.'

    if F2UDF.failed_arts:
        sys.exit(abstract)
    else:
        print >> sys.stderr, abstract

if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('-p', dest = 'pid',
                       help='Lims id for current Process')
    parser.add_argument('-f', dest='result_file', default=None,
                       help=(''))


    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args)

