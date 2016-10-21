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

    def get_app_tag_details(self):
        app_tag = sample.udf['Sequencing Analysis']
        app_tag_versions = ApplicationDetails.query.filter_by(application_tag = app_tag).first()
        latest_version = 0
        for version in app_tag_versions:
            if int(version.version) > latest_version:
                latest_version = version.version
        sample.udf['Application Tag Version'] = latest_version
        sample.put()

    def check_sample_id()
        ###kolla bokstaver, siffror, samt "-" (bindestreck)

    def set_reads_missing(self):
        app_tag = sample.udf['Sequencing Analysis']
        reads_missing = 0.75*parse_application_tag(app_tag)['reads']/1000000
        self.sample.udf['Reads missing (M)'] = reads_missing

    def check_duplicated_sample_names(self):
        """om ett prov namn förekommer på två prover inom samma customer så kolla om gamla provets udf "cancelled"==yes, annars varna
        """
        dup_samps = get_samples(name = self.sample_name, udf={'customer' : self.udfs['customer']})
        for dup_samp in dup_samps:
            if samp.id != self.sample.id:
                dup_samp_udfs = dict(dup_samp.udf.items())
                if "cancelled" in dup_samp_udfs and dup_samp_udfs["cancelled"] == 'yes':
                    ### 'no problem'
                else:
                    ### 'warn'
                

    def check_familyID(self):
        samps_to_check = get_samples(udf={'customer' : self.udfs['customer'], 'familyID' : self.udfs['familyID']})
        for samp in samps_to_check:
            if samp.id != self.sample.id:
                samp_udfs = dict(samp.udf.items())
                if 'motherID' in samp_udfs or 'fatherID' in samp_udfs:
                elif
                samp.udf['motherID']
                'fatherID'
        #om ett familjeid+customer fins i lims redan:
        #    Kolla om barn: dvs om den nya har mother och/eller father:
        #        om ja så ok
        #        annars:
        #            kolla om parrent to fins:
        #                om ja:
        #                     och sätt barnets mother/father
        #                annars:
        #                    varna fail

    def check_family_relations(self):
        #Om udferna mammas namn eller pappas namn är satta, kolla att de fins i lims, faila eller varna om inte

    def check_trio(self):
        #om tre prov innom samma projekt har application tag som börjar med WGS och har samma family id, så byt till WGT

    def check_volume(self):
        #om RML, EXX, WGX prov så volym inte requiered. Men annas

    def check_capture_kit(self):
        #om EXX så måste finnas capture kit

    def check_gene_list(self):
        #om genlista så separera alltid med endast ;. Om något annat, byt ut




class GetLimsData():
    def __init__(self, process):
        self.process = process
        self.samples = []
        self.passed_arts = []
        self.failed_arts = []
        self.sample_info = {}
        self.process_info = {}



    def format_data(self):
        all_artifacts = self.process.all_inputs(unique=True)
        artifacts = filter(lambda a: a.output_type == "Analyte" , all_artifacts)
        self.samples = list(set([a.samples[0] for a in artifacts]))
        for samp in self.samples:
            s_id = samp.id
            udfs = samp.udf
            self.sample_info[s_id] = {'Prov':'',
                        'Clinical Genomics ID':'',
                        'Analys':'',
                        'Order ID':'',
                        'Kommentar':'',
                        'Pris':''}
            ##try except...
            app_tag = udfs['Sequencing Analysis']
            priority = udfs['priority']
            version = udfs['Application Tag Version']
            price = self._price(app_tag, priority, version)
            self.sample_info[s_id]['Prov'] = samp.name
            self.sample_info[s_id]['Clinical Genomics ID'] = samp.id
            self.sample_info[s_id]['Analys'] = app_tag
            self.sample_info[s_id]['Kommentar'] = samp.date_received
            self.sample_info[s_id]['Order ID'] = samp.project.name
            self.sample_info[s_id]['Pris'] = price 


def main(lims, pid): # aggregate
    process = Process(lims, id = pid)
    GLD = GetLimsData(process) #aggregate
    GLD.format_data()

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

    main(lims, args.pid,  args.file)

