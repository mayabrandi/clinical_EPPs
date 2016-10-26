import os
import sys
import logging

import xlsxwriter
from argparse import ArgumentParser
from genologics.lims import Lims
from genologics.config import BASEURI, USERNAME, PASSWORD
from genologics.entities import Process
from genologics.epp import EppLogger
from genologics.epp import set_field

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from clinicaladmin.database import db, app, ApplicationDetails, ApplicationTagData, MethodDescription, Customers
from lims.utils.core import parse_application_tag


from datetime import date


DESC = """"""




class SampleReceptionControle():
    def __init__(self, sample):
        self.sample = sample
        self.sample_name = sample.name        
        self.udfs = sample.udf

    def app_tag_version(self):
        ## Get app tag version from db and set sample udf
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

#    def check_sample_id()
#        ###kolla bokstaver, siffror, samt "-" (bindestreck)
#
#    def set_reads_missing(self):
#        app_tag = sample.udf['Sequencing Analysis']
#        target_amount = parse_application_tag(app_tag)['reads']/1000000
#        self.sample.udf['Reads missing (M)'] = target_amount
#
#    def check_duplicated_sample_names(self):
#        """om ett prov namn forekommer pa tva prover inom samma customer sa kolla om gamla provets udf "cancelled"==yes, annars varna
#        """
#        dup_samps = get_samples(name = self.sample_name, udf={'customer' : self.udfs['customer']})
#        for dup_samp in dup_samps:
#            if samp.id != self.sample.id:
#                dup_samp_udfs = dict(dup_samp.udf.items())
#                if "cancelled" in dup_samp_udfs and dup_samp_udfs["cancelled"] == 'yes':
#                    ### 'no problem'
#                else:
#                    ### 'warn'
#                
#
#    def check_familyID(self):
#        samps_to_check = get_samples(udf={'customer' : self.udfs['customer'], 'familyID' : self.udfs['familyID']})
#        for samp in samps_to_check:
#            if samp.id != self.sample.id:
#                samp_udfs = dict(samp.udf.items())
#                if 'motherID' in samp_udfs or 'fatherID' in samp_udfs:
#                elif
#                samp.udf['motherID']
#                'fatherID'
#        #om ett familjeid+customer fins i lims redan:
#        #    Kolla om barn: dvs om den nya har mother och/eller father:
#        #        om ja sa ok
#        #        annars:
#        #            kolla om parrent to fins:
#        #                om ja:
#        #                     och satt barnets mother/father
#        #                annars:
#        #                    varna fail
#
#    def check_family_relations(self):
#        #Om udferna mammas namn eller pappas namn ar satta, kolla att de fins i lims, faila eller varna om inte
#
#    def check_trio(self):
#        #om tre prov innom samma projekt har application tag som borjar med WGS och har samma family id, sa byt till WGT
#
#    def check_volume(self):
#        #om RML, EXX, WGX prov sa volym inte requiered. Men annas
#
#    def check_capture_kit(self):
#        #om EXX sa maste finnas capture kit
#
#    def check_gene_list(self):
#        #om genlista sa separera alltid med endast ;. Om nagot annat, byt ut




class ReceptionControle():
    def __init__(self, process):
        self.process = process
        self.samples = []
       # self.passed_arts = []
       # self.failed_arts = []

    def get_samples(self):
        all_artifacts = self.process.all_inputs(unique=True)
        artifacts = filter(lambda a: a.output_type == "Analyte" , all_artifacts)
        self.samples = list(set([a.samples[0] for a in artifacts]))

    def check_samples(self):
        for samp in self.samples:
            SRC = SampleReceptionControle(samp)
            SRC.app_tag_version()

def main(lims, pid): 
    process = Process(lims, id = pid)
    RC = ReceptionControle(process)
    RC.get_samples()
    RC.check_samples()

#    d = {'ca': len(EBV.passed_arts),
#         'ia': len(EBV.failed_arts)}
#    abstract = ("Updated {ca} artifact(s), skipped {ia} artifact(s) with "
#                "wrong and/or blank values for some udfs.").format(**d)
#
#    print >> sys.stderr, abstract # stderr will be logged and printed in GUI


if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('-p', default = None , dest = 'pid',
                        help='Lims id for current Process')
    args = parser.parse_args()
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()

    main(lims, args.pid)

