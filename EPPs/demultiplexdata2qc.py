#!/usr/bin/env python
DESC="""EPP script to set qc-falgs based on Q30 and #Reads


Maya Brandi
Science for Life Laboratory, Stockholm, Sweden
""" 
from argparse import ArgumentParser
from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD
from genologics.entities import Process
from genologics.epp import EppLogger
from genologics.epp import set_field
import logging
import sys



class Demux2QC:
    def __init__(self, process):
        self.process = process
        self.artifacts = []
        self.q30treshhold = None
        self.reads_treshold = None
        self.passed_arts = 0
        self.failed_arts = 0

    def set_tresholds(self):
        if 'Threshold for % bases >= Q30' in self.process.udf:
            self.q30treshhold = float(self.process.udf['Threshold for % bases >= Q30'])
        else:
            sys.exit('Threshold for % bases >= Q30 has not ben set.')
        self.reads_treshold = 1000

    def get_artifacts(self):
        all_artifacts = self.process.all_outputs(unique=True)
        self.artifacts = filter(lambda a: a.output_type == "ResultFile" , all_artifacts)

    def set_qc(self):
        for artifact in self.artifacts:
            if '# Reads' in artifact.udf and '% Bases >=Q30' in artifact.udf:
                q30 = float(artifact.udf['% Bases >=Q30'])
                reads = int(artifact.udf['# Reads'])
                if q30 >= self.q30treshhold and reads >= self.reads_treshold:
                    artifact.qc_flag = 'PASSED'
                else:
                    artifact.qc_flag = 'FAILED'
                artifact.put()
                self.passed_arts += 1
            else:
                self.failed_arts += 1

def main(lims,args):
    process = Process(lims, id = args.pid)
    D2QC = Demux2QC(process)
    D2QC.get_artifacts()
    D2QC.set_tresholds()
    D2QC.set_qc()

    d = {'ca': D2QC.passed_arts,
         'ia': D2QC.failed_arts }

    abstract = ("Updated {ca} artifact(s), skipped {ia} artifact(s) with "
                "wrong and/or blank values for some udfs.").format(**d)

    if D2QC.failed_arts:
        sys.exit(abstract)
    else:
        print >> sys.stderr, abstract


if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('-p', dest = 'pid',
                        help='Lims id for current Process')
    parser.add_argument('-l', dest = 'log',
                        help='Log file for runtime info and errors.')
    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()

    main(lims, args)
