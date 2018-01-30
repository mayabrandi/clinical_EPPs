#!/usr/bin/env python
from __future__ import division
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process
from genologics.epp import EppLogger

from openpyxl import load_workbook
import json
from statistics import mean, median
import numpy
from clinical_EPPs import WELL_TRANSFORMER
import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile


import logging
import sys

DESC = """epp script to ...
    dilution_file   - qPCR Result file. Uploded by user.

Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""


class QpcrDilution():

    def __init__(self, process, log):
        self.log = log 
        self.process = process
        self.artifacts = {}
        self.passed_arts = 0
        self.failed_arts = 0
        self.dilution_data = {}
        self.removed_replicates = 0

    def get_artifacts(self):
        in_arts = self.process.all_inputs(unique=True)
        all_artifacts = self.process.all_outputs(unique=True)
        out_artifacts = filter(lambda a: a.output_type == "ResultFile" , all_artifacts)
        for a in in_arts:
            samp = a.samples[0].id
            self.artifacts[samp] = {'in': a}
        for a in out_artifacts:
            samp = a.samples[0].id
            self.artifacts[samp]['out'] = a

    def get_file(self):
        try:
            for f in self.process.shared_result_files():
                if f.name =='qPCR Result File':
                    qPCR_file = f.files[0]
            return qPCR_file.content_location.split('scilifelab.se')[1]
        except:
            sys.exit('could not read dilutionfile')


    def make_dilution_data(self, dilution_file):
        dilution_file = self.get_file()
        df = pd.read_excel(dilution_file)
        for self.index, row in df.iterrows():
            well = row['Well']
            Cq = round(row['Cq'],3)
            SQ = row['Starting Quantity (SQ)']
            if not (numpy.isnan(Cq) or numpy.isnan(SQ)):
                orwell = WELL_TRANSFORMER[well]['well']
                dilut = WELL_TRANSFORMER[well]['dilut']
                if dilut in ['1E03','2E03','1E04']:
                    if not orwell in self.dilution_data.keys():
                        self.dilution_data[orwell] = {
                            'SQ' : {'1E03':[],'2E03':[],'1E04':[]},
                            'Cq' : {'1E03':[],'2E03':[],'1E04':[]}}
                    self.dilution_data[orwell]['SQ'][dilut].append(SQ)
                    self.dilution_data[orwell]['Cq'][dilut].append(Cq)

    def set_udf(self):
        for samp_id, art in self.artifacts.items():
            self.log.write('\n############################################\n')
            self.log.write('Sample: ' + samp_id + '\n')
            PA = PerArtifact(art, self.dilution_data, samp_id, self.log)
            PA.check_dilution_range()
            PA.check_distance_find_outlyer()
            for dil in PA.index.keys():
                self.log.write(dil + ' Measurements : ' + str(PA.Cq[dil])+'\n')
                if PA.index[dil] is not None:
                    self.removed_replicates += 1
                    self.log.write('Removed measurement: ' + str(PA.poped_dilutes[dil]) + '\n')
            passed = PA.calculate_molar()
            if passed:
                self.passed_arts +=1
            else:
                self.failed_arts +=1


class PerArtifact():
    """Artifact specific class do determine messuement outlyers and calculate dilution"""
    def __init__(self, artifact, dilution_data, sample_id, log):
        self.log = log
        self.sample_id = sample_id
        self.dilution_data = dilution_data
        self.artifact = artifact
        self.size_bp = 470
        self.outart = artifact['out']
        self.well = self.outart.location[1]
        self.Cq = { '1E03' : self.dilution_data[self.well]['Cq']['1E03'], 
                    '2E03' : self.dilution_data[self.well]['Cq']['2E03'], 
                    '1E04' : self.dilution_data[self.well]['Cq']['1E04']}
        self.index = {'1E03' : None, '2E03' : None, '1E04' : None}
        self.poped_dilutes = {'1E03' : None, '2E03' : None, '1E04' : None}


    def check_dilution_range(self):
        for dil, values in self.Cq.items():
            error_msg = 'To vide range of values for dilution: ' + dil + ' : ' + str(values)
            array = numpy.array(self.Cq[dil])   
            diff_from_mean = numpy.absolute(array - mean(array))
            while max(self.Cq[dil])-min(self.Cq[dil])> 0.4:
                if self.index[dil] is not None:
                    sys.exit(error_msg)
                else:
                    ind = numpy.argmax(diff_from_mean)
                    self.index[dil] = ind
                    self.poped_dilutes[dil] = self.Cq[dil].pop(ind)
                    print self.poped_dilutes[dil]
                    array = numpy.array(self.Cq[dil])
                    diff_from_mean = numpy.absolute(array - mean(array))
                    

    def check_distance_find_outlyer(self):
        D1_in_range, D2_in_range = self.check_distance()
        while not (D1_in_range and D2_in_range):
            self.find_outlyer(D1_in_range, D2_in_range)
            for dilute, ind in self.index.items():
                if ind is not None:
                    self.poped_dilutes[dilute] = self.Cq[dilute].pop(ind) 
                    print 'kkkk'
                    print self.poped_dilutes[dilute]
            D1_in_range, D2_in_range = self.check_distance()            


    def check_distance(self):
        """Compares the difference between the mean of the triplicates for the different dilutions. 
        Checkes wether the differences are within accepted ranges"""
        D1 = mean(self.Cq['1E04'])-mean(self.Cq['1E03'])
        D1_in_range = 2.5 < D1 < 5
        D2 = mean(self.Cq['2E03'])-mean(self.Cq['1E03'])   
        D2_in_range = 0.7 < D2 < 1.5
        return D1_in_range, D2_in_range

    def find_outlyer(self, D1_in_range, D2_in_range):
        control_1E03 = False
        if not D1_in_range:
            array = numpy.array(self.Cq['1E03'])
            diff_from_mean_1E03 = numpy.absolute(array - mean(array))
            outlyer_1E03 = max(diff_from_mean_1E03)
            array = numpy.array(self.Cq['1E04'])
            diff_from_mean_1E04 = numpy.absolute(array - mean(array)) 
            outlyer_1E04 = max(diff_from_mean_1E04)
            if outlyer_1E03 > outlyer_1E04:
                if self.index['1E03'] is not None:
                    self.log.write('1E03 Measurements : ' + str(self.Cq['1E03']) + '\n')
                    self.log.write('Removed measurement: ' + str(self.poped_dilutes['1E03']) + '\n')
                    self.log.write('One outlyer removed, but distance still to big. Skript excited.')
                    sys.exit('Distance to big, tryed to remove outlyer but distance still not within range')
                else:
                    control_1E03 = True
                    self.index['1E03'] = numpy.argmax(diff_from_mean_1E03)
            else:
                if self.index['1E04'] is not None:
                    self.log.write('1E04 Measurements : ' + str(self.Cq['1E04']) + '\n')
                    self.log.write('Removed measurement: ' + str(self.poped_dilutes['1E04']) + '\n')
                    self.log.write('One outlyer removed, but distance still to big. Skript excited.')
                    sys.exit('Distance to big, tryed to remove outlyer but distance still not within range')
                else:
                    self.index['1E04'] = numpy.argmax(diff_from_mean_1E04)
        if not D2_in_range:
            array = numpy.array(self.Cq['2E03'])
            diff_from_mean_2E03 = numpy.absolute(array - numpy.median(array))/numpy.median(array).tolist()
            outlyer_2E03 = max(diff_from_mean_2E03)
            array = numpy.array(self.Cq['1E03'])
            diff_from_mean_1E03 = numpy.absolute(array - numpy.median(array))/numpy.median(array).tolist()
            outlyer_1E03 = max(diff_from_mean_1E03)
            if outlyer_2E03 > outlyer_1E03:
                if self.index['2E03'] is not None:
                    self.log.write('2E03 Measurements : ' + str(self.Cq['2E03']) + '\n')
                    self.log.write('Removed measurement: ' + str(self.poped_dilutes['2E03']) + '\n')
                    self.log.write('One outlyer removed, but distance still to big. Skript excited.')
                    sys.exit('Distance to big, tryed to remove outlyer but distance still not within range')
                else:
                    self.index['2E03'] = numpy.argmax(diff_from_mean_2E03)
            else:
                if self.index['1E03']:
                    if control_1E03 and self.index['1E03'] != numpy.argmax(outlyer_1E03):
                        sys.exit('Distance to big. Conflicting outlyers. ')
                    elif not control_1E03:
                        self.log.write('1E03 Measurements : ' + str(self.Cq['1E03']) + '\n')
                        self.log.write('Removed measurement: ' + str(self.poped_dilutes['1E03']) + '\n')
                        self.log.write('One outlyer removed, but distance still to big. Skript excited.')
                        sys.exit('Distance to big, tryed to remove outlyer but distance still not within range')            
                else:
                    self.index['1E03'] = numpy.argmax(diff_from_mean_1E03)
        return self.index


    def calculate_molar(self):
        for dilute, ind in self.index.items():
            if ind is not None:
                self.dilution_data[self.well]['SQ'][dilute].pop(ind)
                # removing outlyer
        SQ_1E03 = mean(self.dilution_data[self.well]['SQ']['1E03'])
        SQ_2E03 = mean(self.dilution_data[self.well]['SQ']['2E03'])
        SQ_1E04 = mean(self.dilution_data[self.well]['SQ']['1E04'])
        orig_conc = (SQ_1E03*1000+SQ_2E03*2000+SQ_1E04*10000)/3
        size_adjust_conc_M = orig_conc*(452/self.size_bp)
        size_adjust_conc_nM= size_adjust_conc_M*1000000000

        try:
            self.outart.udf['Concentration'] = size_adjust_conc_M
            self.outart.udf['Size (bp)'] = int(self.size_bp)
            self.outart.udf['Concentration (nM)'] = size_adjust_conc_nM
            if self.outart.udf['Concentration (nM)'] < 2:
                self.outart.qc_flag = "FAILED"
            else:
                self.outart.qc_flag = "PASSED"
            self.outart.put()
            return True
        except:
            return False 

    

def main(lims, args):
    log = open(args.log, 'a')
    process = Process(lims, id = args.pid)
    QD = QpcrDilution(process, log)
    QD.get_artifacts()
    QD.make_dilution_data(args.dil_file)
    QD.set_udf()

    d = {'ca': QD.passed_arts,
         'ia': QD.failed_arts}
    abstract = ("Updated {ca} artifact(s), skipped {ia} artifact(s) with "
                "wrong and/or blank values for some udfs.").format(**d)
   
    if QD.removed_replicates:
        abstract += ' WARNING: Removed replicate from ' +str(QD.removed_replicates)+ ' samples. See log file for details.'  

 
    log.close()
    if QD.failed_arts:
        sys.exit(abstract)
    else:
        print >> sys.stderr, abstract

if __name__ == "__main__":
    # Initialize parser with standard arguments and description
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid',
                       help='Lims id for current Process')
    parser.add_argument('--log', default=sys.stdout,
                       help=('File name for standard log file, '
                              'for runtime information and problems.'))
    parser.add_argument('--dil_file', default=None,
                       help=('File name for qPCR result file.'))

    args = parser.parse_args()
    if not args.dil_file:
        sys.exit('Dilution File missing!')

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args)
