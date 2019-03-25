#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import logging

from argparse import ArgumentParser
from genologics.lims import Lims
from genologics.config import BASEURI, USERNAME, PASSWORD
from genologics.entities import Process

from clinical_EPPs.config import CG_URL
from cgface.api import CgFace

DESC = """"""

class ReceptionControle():
    def __init__(self, process):
        self.process = process
        self.samples = []
        self.log = None
        self.failed_samples = 0
        self.cgface_obj = CgFace(url=CG_URL)
        self.sample_qc = True

    def set_reads_missing(self, sample):
        """Sets the 'Reads missing (M)' udf, based on the application tag"""
        try:
            app_tag = sample.udf['Sequencing Analysis']
            target_amount = self.cgface_obj.apptag(tag_name = app_tag, key = 'target_reads')
            sample.udf['Reads missing (M)'] = target_amount/1000000
            sample.put()
            sample_qc = True
        except:
            self.log.write("Failed to get 'Reads missing' from Application tag: "+app_tag)
            self.sample_qc = False

    def reception_control_log(self, res_file):
        try:
            self.log = open(res_file, 'a')
        except:
            sys.exit('Could not open log file')

    def get_samples(self):
        all_artifacts = self.process.all_inputs(unique=True)
        artifacts = filter(lambda a: a.output_type == "Analyte" , all_artifacts)
        self.samples = [(a.samples[0], a) for a in artifacts]

    def check_samples(self):
        for samp , art in self.samples:
            self.log.write('\n###  Checking sample ' + samp.id+', with sample name ' + samp.name.encode('utf-8').strip() +" ###\n")
            self.set_reads_missing(samp)
            if self.sample_qc:
                art.qc_flag = "PASSED"
            else:
                self.failed_samples +=1
                art.qc_flag = "FAILED"
            self.sample_qc = True
            art.put()

def main(lims, pid, res_file):
    process = Process(lims, id = pid)
    RC = ReceptionControle(process)
    RC.reception_control_log(res_file)
    RC.get_samples()
    RC.check_samples()
    RC.log.close()


    if RC.failed_samples:
        sys.exit(str(RC.failed_samples)+' failed preparation. See Log, for details.')
    else:
        print >> sys.stderr, 'All samples pased preparation.'


if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('-p', default = None , dest = 'pid',
                        help='Lims id for current Process')
    parser.add_argument('-l', default = None , dest = 'log',
                        help='Log file')
    parser.add_argument('-r', default = None , dest = 'res',
                        help='Reception Contol - log file')
    args = parser.parse_args()
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    logging.basicConfig(filename= args.log,level=logging.DEBUG)
    main(lims, args.pid, args.res)

