#!/usr/bin/env python
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

from datetime import date


DESC = """"""

class GetLimsData():
    def __init__(self, process):
        self.process = process
        self.samples = []
        self.passed_arts = []
        self.failed_arts = []
        self.sample_info = {}
        self.process_info = {}

    def _price(self, app_tag, priority, version):
        app_tag = ApplicationDetails.query.filter_by(application_tag = app_tag, version = version).first()
        price = app_tag.__dict__[priority + '_price']
        return int(price.replace(' ',''))

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

class InvoiceTemplate():
    def __init__(self, workbook, sample_info):
        self.worksheet = workbook.add_worksheet()
        self.worksheet.hide_gridlines(2)
        self.worksheet.set_column('A:F', 12)
        self.sample_info = sample_info

        ## Formates
        self.title_1 = workbook.add_format({
            'bold': 0,
            'size': 18,
            'valign': 'vcenter'})

        self.title_2 = workbook.add_format({
            'bold': 0,
            'size': 14,
            'valign': 'vcenter'})

        self.title_3 = workbook.add_format({
                        'bold' : 1,
                        'size' : 10,
                        'bottom' : 1,
                        'top' : 1,
                        'valign' : 'vcenter',
                        'fg_color' : '#E5E8E8'})

        self.frame_bottom = workbook.add_format({'top': 1,'bottom':1})
        self.default = workbook.add_format({'size': 10})
        self.bold = workbook.add_format({'bold': True, 'size': 10})
        self.row = 5

    def _make_heading_section(self):
        self.worksheet.merge_range('A1:B1', 'Fakturaunderlag', self.title_1)
        self.worksheet.merge_range('A2:B2', 'Clinical Genomics', self.title_2)
        self.worksheet.write('C1', 'KTH', self.title_2)
        self.worksheet.write('E1', 'Nummer',self.default)
        self.worksheet.write('E2', 'Datum',self.default)
        self.worksheet.write('F2', date.today().isoformat() ,self.default)

    def _make_from_section(self):
        r_str = str(self.row)
        self.worksheet.merge_range('A' + r_str + ':F' + r_str , 'From', self.title_3)

        cust_info = [('Enhet','Clinical Genomics'),
                    ('Projektnummer','80210'),
                    ('Kontaktperson','Valtteri Wirta'),
                    ('E-post','valtteri.wirta@scilifelab.se'),
                    ('Telefon','08-5248 1545')]
        for key, val in cust_info:
            self.worksheet.write(self.row, 0, key, self.bold)
            self.worksheet.write(self.row, 1, val, self.default)
            self.row += 1


    def _make_to_section(self):
        self.row+=2
        r_str = str(self.row)
        self.worksheet.merge_range('A' + r_str + ':F' + r_str , 'To', self.title_3)

        invoicer = [('Kontaktperson','Valtteri Wirta'),
                    ('E-post' , 'valtteri.wirta@ki.se'),
                    ('Referens' , 'ZZC1VALWIR'),
                    ('Institution/Avd.' , 'MTC'),
                    ('Fakturaadress' , 'Karolinska Instituet, Fakturor, Box 23 109'),
                    ('Postnummer' , '104 35'),
                    ('Postadress' , 'Stockholm'),
                    ('Land' , 'Sverige')]


        for key, val in invoicer:
            self.worksheet.write(self.row, 0, key, self.bold)
            self.worksheet.write(self.row, 1, val, self.default)
            self.row += 1

    def _make_comments_section(self):
        self.row+=2

        r_str = str(self.row)
        self.worksheet.merge_range('A22:F22', 'Comments', self.title_3)

    def _make_samples_section(self):
        self.row = self.row + 4

        table_heads = ['Prov','Clinical Genomics ID','Analys', 'Order ID','Kommentar','Pris']

        for i, head in enumerate(table_heads):
            self.worksheet.write(self.row, i, head, self.title_3)

        self.row +=1
        r_str0 = str(self.row)
        for key, samp in self.sample_info.items():
            for i, head in enumerate(table_heads):
                if head =='Prov':
                    self.worksheet.write(self.row, i, samp[head], self.bold)
                else:
                    self.worksheet.write(self.row, i, samp[head], self.default)
            self.row += 1

        self.row += 1
        r_str1 = str(self.row)
        self.worksheet.write(self.row, 4, 'Total', self.title_3)
        self.worksheet.write(self.row, 5, '=SUM(F' + r_str0 + ':F' + r_str1 +')',self.title_3)
        srow = str(self.row+1)
        self.worksheet.merge_range('A' + srow + ':D' + srow , '',self.frame_bottom)

    def make_template(self):
        self._make_heading_section()
        self._make_from_section()
        self._make_to_section()
        self._make_comments_section()
        self._make_samples_section()


def main(lims, pid, xlsx_file): # aggregate
    process = Process(lims, id = pid)
    GLD = GetLimsData(process) #aggregate
    GLD.format_data()
    workbook = xlsxwriter.Workbook(xlsx_file+'_invoice.xlsx')
    IT = InvoiceTemplate(workbook, GLD.sample_info)
    IT.make_template()
    workbook.close()

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
    parser.add_argument('-f', dest = 'file',
                        help=('File path to new invoice file'))
    args = parser.parse_args()
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()

    main(lims, args.pid,  args.file)

