#!/usr/bin/env python
from argparse import ArgumentParser
import pandas as pd

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process

import logging
import sys
import os



DESC = """EPP script to generate plate layout

Written by Maya Brandi, Clinical Genomics, Stockholm, Sweden"""


class PlateSetup():
    def __init__(self, process, MAF_file):
        self.process = process
        out_analytes = [a for a in process.all_outputs() if a.type=='Analyte']
        self.rows = map(chr, range(97, 105))
        self.columns = range(1,13)
        self.art_dict = {a.location[1].lower() :  a for a in out_analytes}
        self.plate_name = out_analytes[0].container.name
        self.MAF_file = MAF_file + '_Plate_layout.xls'
        self.headers = []
        self.data = {}

    def make_xls(self):
        for col in self.columns:
            for row in self.rows:
                self.data['Plate'].append(1)
                self.data['Row'].append(row)
                self.data['Column'].append(int(col))
                location = row + ':' + str(col)
                self.data['Project Code'].append(self.plate_name)
                if location in self.art_dict:
                    sample = self.art_dict[location].samples[0]
                    self.data['Sample ID NO'].append('CG-'+ sample.id)
                else:
                    self.data['Sample ID NO'].append('')                    

        df = pd.DataFrame(self.data) 
        df = df[self.headers]
        writer = pd.ExcelWriter(self.MAF_file, engine='xlsxwriter')
        workbook  = writer.book
        format = workbook.add_format()
        format.set_align('center')
        df.to_excel(writer, sheet_name='Sheet1', index=False, startcol=0)
        worksheet = writer.sheets['Sheet1']
        worksheet.set_column('A:B', 18)
        worksheet.set_column('C:E', 8, format)
        
        writer.save()


    def set_header_section(self):
        self.headers = ['Project Code', 'Sample ID NO', 'Plate', 'Row', 'Column']
        self.data = {key : [] for key in self.headers}




def main(lims, args):
    process = Process(lims, id = args.pid)
    PS = PlateSetup(process, args.MAF_file)
    PS.set_header_section()
    PS.make_xls()
    abstract = ''
    
    if abstract:
        logging.warning(abstract)
        sys.exit(abstract)
    else:
        print >> sys.stderr, 'MAF Plate Layout file was succsessfully generated!'

if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('-p', dest = 'pid',
                        help='Lims id for current Process')
    parser.add_argument('-l', dest = 'log', default=sys.stdout,
                        help=('File name for standard log file, '
                              'for runtime information and problems.'))
    parser.add_argument('-f', dest = 'MAF_file',
                        help=('File path to new Plate Layout file'))    
                        
    args = parser.parse_args()
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    logging.basicConfig(
                    level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename = args.log,
                    filemode='w')

    main(lims, args)
