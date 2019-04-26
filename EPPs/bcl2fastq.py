#!/usr/bin/env python
from __future__ import division
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD
from clinical_EPPs.config import SQLALCHEMY_DATABASE_URI

from genologics.entities import Process
from genologics.epp import EppLogger

import logging
import sys

from BeautifulSoup import BeautifulSoup, Comment

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (Column, Integer, String, DateTime, Text, Enum,
                        ForeignKey, UniqueConstraint, Numeric, Date)
from sqlalchemy.orm import relationship, backref

import os


DESC = """
"""

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI 
db = SQLAlchemy(app)


##--------------------------------------------------------------------------------
##----------------------------------MODELS----------------------------------------
##--------------------------------------------------------------------------------

class Project(db.Model):
    __tablename__ = 'project'
    project_id = Column(Integer, primary_key=True)
    projectname = Column(String(255), nullable=False)
    time = Column(DateTime, nullable=False)
    def __repr__(self):
        return (u"{self.__class__.__name__}: {self.project_id}"
                .format(self=self))

class Sample(db.Model):
    __tablename__ = 'sample'
    sample_id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('project.project_id'),
                        nullable=False)
    samplename = Column(String(255), nullable=False)
    barcode = Column(String(255), nullable=True)
    time = Column(db.DateTime, nullable=True)
    project = relationship('Project', backref=backref('samples'))


class Demux(db.Model):
    __tablename__ = 'demux'
    demux_id = Column(Integer, primary_key=True)
    flowcell_id = Column(Integer, ForeignKey('flowcell.flowcell_id'),
                         nullable=False)
    datasource_id = Column(Integer, ForeignKey('datasource.datasource_id'),
                           nullable=False)
    basemask = Column(String(255), nullable=True)
    time = Column(DateTime, nullable=True)
    UniqueConstraint('flowcell', 'basemask', name='demux_ibuk_1')
    datasource = relationship('Datasource', backref=backref('demuxes'))
    flowcell = relationship('Flowcell', backref=backref('demuxes'))


class Datasource(db.Model):
    __tablename__ = 'datasource'
    datasource_id = Column(Integer, primary_key=True)
    supportparams_id = Column(Integer,
                              ForeignKey('supportparams.supportparams_id'),
                              nullable=False)
    runname = Column(String(255), nullable=True)
    machine = Column(String(255), nullable=True)
    rundate = Column(DateTime, nullable=True)
    document_path = Column(String(255), nullable=False)
    document_type = Column(Enum('html', 'xml', 'undefined'), nullable=False,
                           default='html')
    server = Column(String(255), nullable=True)
    time = Column(DateTime, nullable=True)
    supportparams = relationship('Supportparams',
                                 backref=backref('datasources'))

class Supportparams(db.Model):
    __tablename__ = 'supportparams'
    supportparams_id = Column(Integer, primary_key=True)
    document_path = Column(String(255), nullable=False)
    systempid = Column(String(255), nullable=True)
    systemos = Column(String(255), nullable=True)
    systemperlv = Column(String(255), nullable=True)
    systemperlexe = Column(String(255), nullable=True)
    idstring = Column(String(255), nullable=True)
    program = Column(String(255), nullable=True)
    commandline = Column(Text)
    sampleconfig_path = Column(String(255), nullable=True)
    sampleconfig = Column(Text)
    time = Column(DateTime, nullable=True)


class Flowcell(db.Model):
    __tablename__ = 'flowcell'
    flowcell_id = Column(Integer, primary_key=True)
    flowcellname = Column(String(255), nullable=False)
    flowcell_pos = Column(Enum('A', 'B'), nullable=False)
    time = Column(DateTime)
    UniqueConstraint('flowcellname', name='flowcellname')
    datasource = relationship('Demux', backref=backref('flowcells'))

class Unaligned(db.Model):
    __tablename__ = 'unaligned'
    unaligned_id = Column(Integer, primary_key=True)
    sample_id = Column(Integer, ForeignKey('sample.sample_id'), nullable=False)
    demux_id = Column(Integer, ForeignKey('demux.demux_id'), nullable=False)
    lane = Column(Integer, nullable=True)
    yield_mb = Column(Integer, nullable=True)
    passed_filter_pct = Column(Numeric(10, 5), nullable=True)
    readcounts = Column(Integer, nullable=True)
    raw_clusters_per_lane_pct = Column(Numeric(10, 5), nullable=True)
    perfect_indexreads_pct = Column(Numeric(10, 5), nullable=True)
    q30_bases_pct = Column(Numeric(10, 5), nullable=True)
    mean_quality_score = Column(Numeric(10, 5), nullable=True)
    time = Column(DateTime, nullable=True)
    demux = relationship('Demux', backref=backref('unaligned'))
    sample = relationship('Sample', backref=backref('unaligned'))




##--------------------------------------------------------------------------------
##--------------------------------LIMS EPP----------------------------------------
##--------------------------------------------------------------------------------

class BCLconv():
    def __init__(self, process):
        self.process = process
        self.artifacts = {}
        self.passed_arts = 0
        all_artifacts = self.process.all_outputs(unique=True)
        self.total_nr_arts = len(filter(lambda a: a.output_type == "ResultFile" , all_artifacts))
        self.demux_data = []


    def get_artifacts(self):
        """Prepparing output artifact dict."""
        for input_output in self.process.input_output_maps:
            inpt = input_output[0]
            outpt = input_output[1]
            if outpt['output-generation-type'] != 'PerAllInputs':
                art = outpt['uri']
                sampname = art.samples[0].id  
                well = inpt['uri'].location[1][0]
                if not sampname in self.artifacts:
                    self.artifacts[sampname] = {well: art}
                else: 
                    self.artifacts[sampname][well] = art         

    def get_fc_id(self):
        """Gettning FC id of the seq-run.
        Can't come up with a better way of doing this..."""
        try:
            self.flowcellname = self.process.all_inputs()[0].container.name
        except:
            sys.exit('Could not get FC id from Container name')


    def get_demux_data(self):
        """Geting the demultiplex statistics from the demultiplex database csdb."""
        try:
            self.demux_data = Unaligned.query.join(Demux).join(Flowcell).filter(Flowcell.flowcellname == self.flowcellname).all()
        except:
            sys.exit('Error getting data from the demultiplexing database. Maybe the flowcell id is wrong: '+ self.flowcellname)

    def set_udfs(self):
        """Setting the demultiplex udfs"""
        for samp in self.demux_data:
            #The sample.samplename in the demux database corresponds to the LIMS <sample.id>_<index>
            sample_name = samp.sample.samplename.split('_')[0]
            try:
                art = self.artifacts[sample_name][str(samp.lane)]
                art.udf['% Perfect Index Read'] =  float(samp.perfect_indexreads_pct)
                art.udf['# Reads'] =  samp.readcounts
                art.udf['% Bases >=Q30'] =  float(samp.q30_bases_pct)
                art.put()
                self.passed_arts += 1
            except:
                pass


def main(lims, args):
    process = Process(lims, id = args.pid)
    BCL = BCLconv(process)
    BCL.get_fc_id()
    BCL.get_artifacts()
    BCL.get_demux_data()
    BCL.set_udfs()


    d = {'ca': BCL.passed_arts,'wa' : BCL.total_nr_arts - BCL.passed_arts}
    abstract = ("Updated {ca} artifact(s). Skipped {wa} due to missing data in the demultiplex database.").format(**d)

    print >> sys.stderr, abstract

if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('-p', dest = 'pid',
                        help='Lims id for current Process')
    parser.add_argument('-l', dest = 'log', default=sys.stdout,
                        help=('File name for standard log file, '
                              'for runtime information and problems.'))

    args = parser.parse_args()
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args)
