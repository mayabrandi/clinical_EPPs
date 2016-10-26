#!/usr/bin/env python
import os
import sys
import logging
from datetime import date


DESC = """"""


class InvoiceTemplate():
    def __init__(self, workbook):
        self.worksheet = workbook.add_worksheet()
        self.worksheet.hide_gridlines(2)
        self.worksheet.set_column('A:F', 12)

        ## formats
        self.money_format = workbook.add_format({'num_format': '# kr'})
        self.total_price_format = workbook.add_format({
                        'bold' : 1,
                        'size' : 10,
                        'bottom' : 1,
                        'top' : 1,
                        'valign' : 'vcenter',
                        'fg_color' : '#E5E8E8',
                        'num_format': '# kr'})
        self.format_title_1 = workbook.add_format({
            'bold': 0,
            'size': 18,
            'valign': 'vcenter'})

        self.format_title_2 = workbook.add_format({
            'bold': 0,
            'size': 14,
            'valign': 'vcenter'})

        self.format_title_3 = workbook.add_format({
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

    def make_heading_section(self, invoicer, invoice_ref):
        self.worksheet.merge_range('A1:B1', 'Fakturaunderlag', self.format_title_1)
        self.worksheet.merge_range('A2:B2', 'Clinical Genomics', self.format_title_2)
        self.worksheet.write('C1', invoicer, self.format_title_2)
        self.worksheet.write('E1', 'Nummer', self.default)
        self.worksheet.write('F1', invoice_ref, self.default)
        self.worksheet.write('E2', 'Datum',self.default)
        self.worksheet.write('F2', date.today().isoformat() ,self.default)

    def make_from_section(self, from_info):
        row_range = 'A' + str(self.row) + ':F' + str(self.row) 
        self.worksheet.merge_range(row_range, 'From', self.format_title_3)
        for key, val in from_info:
            self.worksheet.write(self.row, 0, key, self.bold)
            self.worksheet.write(self.row, 2, val, self.default)
            self.row += 1


    def make_to_section(self, to_info):
        self.row+=2
        row_range = 'A' + str(self.row) + ':F' + str(self.row) 
        self.worksheet.merge_range(row_range , 'To', self.format_title_3)
        for key, val in to_info:
            self.worksheet.write(self.row, 0, key, self.bold)
            self.worksheet.write(self.row, 2, val, self.default)
            self.row += 1

    def make_comments_section(self, comments):
        self.row+=2
        row_range = 'A' + str(self.row) + ':F' + str(self.row)
        self.worksheet.merge_range(row_range , 'Comments', self.format_title_3)
        for key, val in comments:
            self.worksheet.write(self.row, 0, key, self.bold)
            self.worksheet.write(self.row, 2, val, self.default)
            self.row += 1


    def make_samples_section(self, sample_info):
        self.row = self.row + 4
        table_heads = ['Prov','Clinical Genomics ID','Analys', 'Order ID','Kommentar','Pris']
        
        ##  making header
        for i, head in enumerate(table_heads):
            self.worksheet.write(self.row, i, head, self.format_title_3)

        self.row +=1
        r_str0 = str(self.row)
        
        ##  adding samples
        for key, samp in sample_info.items():
            for i, head in enumerate(table_heads):
                if head =='Prov':
                    self.worksheet.write(self.row, i, samp[head], self.bold)
                elif head == 'Pris':
                    self.worksheet.write(self.row, i, samp[head], self.money_format)
                else:
                    self.worksheet.write(self.row, i, samp[head], self.default)
            self.row += 1

        self.row += 1
        r_str1 = str(self.row)

        ##  total price
        self.worksheet.write(self.row, 4, 'Total', self.format_title_3)
        self.worksheet.write(self.row, 5, '=SUM(F' + r_str0 + ':F' + r_str1 +')', self.total_price_format)

        ##  bottom frame
        srow = str(self.row+1)
        self.worksheet.merge_range('A' + srow + ':D' + srow , '',self.frame_bottom)


