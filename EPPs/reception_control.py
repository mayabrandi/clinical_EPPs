#!/usr/bin/env python
import os
import sys
import logging

import xlsxwriter
from argparse import ArgumentParser
from genologics.lims import Lims
from genologics.config import BASEURI, USERNAME, PASSWORD
from genologics.entities import Process
from genologics.epp import set_field

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from clinicaladmin.database import db, app, ApplicationDetails, ApplicationTagData, MethodDescription, Customers
from clinical_EPPs.EPP_utils import parse_application_tag


from datetime import date


DESC = """"""




class SampleReceptionControle():
    def __init__(self, sample, rec_log):
        self.log = rec_log
        self.sample = sample
        self.sample_name = sample.name        
        self.udfs = sample.udf
        self.all_right = True

    def app_tag_version(self):
        """Gets latest app tag version from admin database.
        Sets 'Application Tag Version' udf on sample."""
        app_tag = self.sample.udf['Sequencing Analysis']
        app_tag_versions = ApplicationDetails.query.filter_by(application_tag = app_tag).all()
        if not app_tag_versions:
            sys.exit('Application tag '+app_tag + ' does not exist in ApplicationDetails table in the admin database.')        
        latest_version = 0
        for version in app_tag_versions:
            if int(version.version) > latest_version:
                latest_version = version.version
        self.sample.udf['Application Tag Version'] = latest_version
        self.sample.put()

    def check_sample_name(self):
        """Warning if sample name is not alphanumeric. 
        Exception for '-', witch is allowed."""
        no_dash = self.sample.name.replace('-','')
        if not no_dash.isalnum():
            self.log.write('    FAIL: Sample name not ok!\n')
            self.all_right = False

    def set_reads_missing(self):
        """Sets the 'Reads missing (M)' udf, based on the application tag"""
        app_tag = self.sample.udf['Sequencing Analysis']
        target_amount = parse_application_tag(app_tag)['reads']/1000000
        self.sample.udf['Reads missing (M)'] = target_amount
        self.sample.put()

    def check_duplicated_sample_names(self):
        """If the sample name appears more then once within the same cus, check 
        that the old samp has "cancelled"==yes, otherwise warning!"""
        dup_samps = lims.get_samples(name = self.sample_name, udf={'customer' : self.udfs['customer']})
        for dup_samp in dup_samps:
            if dup_samp.id != self.sample.id:
                if "cancelled" in dup_samp.udf and dup_samp.udf["cancelled"] == 'yes':
                    self.log.write('    INFO: NP! dup samp name but one is canceled\n')
                else:
                    self.log.write("    FAIL: Sample name duplicates: "+dup_samp.name+'\n')
                    self.all_right = False                

    def check_family_members_has_relations(self):
        """Warns if sample has family members (same familyID), but no relation to any of them."""
        samps_to_check = lims.get_samples(udf={'customer' : self.udfs['customer'], 'familyID' : self.udfs['familyID']})
        relation = False
        for samp_to_check in samps_to_check:
            if samp_to_check.id != self.sample.id:
                relation = self.check_relation(self.sample, samp_to_check)
                if not relation:
                    relation = self.check_relation(samp_to_check, self.sample)
                if relation:
                    break 
        if not relation:
            self.log.write("    FAIL: Sample has no relation to any of its family members. Set mohterID, fatherID ore other relation.\n") 
            self.all_right = False

    def check_relation(self, s1, s2):
        """Is s2 mother, father ore other relation to s1?"""
        relation = []
        for k, v in s1.udf.items():
            if k in ['motherID', 'fatherID', 'Other relations']:
                relation.append(v)
        if s2.name in relation:
            return True
        else:
            return False

    def check_family_relations_exists(self):
        """If there are relatives specifyed (mother, father, other), 
        do they exist in lims? Warns if not."""
        missing_relatives = {}
        for k, v in self.sample.udf.items():
            if k in ['motherID', 'fatherID', 'Other relations']:
                relative = lims.get_samples(name = v,  udf={'customer' : self.udfs['customer'], 'familyID' : self.udfs['familyID']})
                if not relative:
                    missing_relatives[k]=v
        if missing_relatives:
            self.log.write("    FAIL: The following relation(s) were set: "+str(missing_relatives)+", but the given sample name(s) do not exist within the family\n")
            self.all_right = False

    def check_trio(self):
        """If thre samples in one family has apptag, beginning with WGS, change to WGT"""
        ##  This function should be recursive to handle more than one trio.
        relatives = lims.get_samples(udf={'customer' : self.udfs['customer'], 'familyID' : self.udfs['familyID']})
        trio = []
        for samp in relatives:
            if samp.udf['Sequencing Analysis'] == 'WGSPCFC030':
                trio.append(samp)
        if len(trio) > 2:
            for samp in trio[0:3]:
                samp.udf['Sequencing Analysis'] = 'WGTPCFC030' 
                samp.put()
            self.log.write("    INFO: application tag WGSPCFC030, switched to WGTPCFC030 on samples: "+', '.join(trio[0:3])+"\n")

    def check_capture_kit(self):
        """Warns if 'Capture Library version' == NA but application tag begins with EXX"""
        appt = self.sample.udf['Sequencing Analysis']
        captb = self.sample.udf['Capture Library version']
        if appt[0:3] == 'EXX' and captb == 'NA':
            self.log.write("    FAIL: 'Capture Library version' is set to NA and has to be changed!")
            self.all_right = False

class ReceptionControle():
    def __init__(self, process):
        self.process = process
        self.samples = []
        self.log = None 
        self.failed_samples = 0

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
            self.log.write('\n###  Checking sample ' + samp.id+', with sample name ' + samp.name +" ###\n")
            SRC = SampleReceptionControle(samp, self.log)
            SRC.app_tag_version()
            #SRC.check_sample_name()
            #SRC.set_reads_missing()
            #SRC.check_duplicated_sample_names()
            #SRC.check_family_members_has_relations()
            #SRC.check_family_relations_exists()
            #SRC.check_trio()
            if not SRC.all_right:
                self.failed_samples +=1
                art.qc_flag = "FAILED"
            else:
                art.qc_flag = "PASSED"
            art.put()

def main(lims, pid, res_file): 
    process = Process(lims, id = pid)
    RC = ReceptionControle(process)
    RC.reception_control_log(res_file)
    RC.get_samples()
    RC.check_samples()
    RC.log.close()


    if RC.failed_samples:
        sys.exit(str(RC.failed_samples)+' failed reception controle. See Order Form Check Log, for details.')
    else:
        print >> sys.stderr, 'All samples pased reception control.'


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

