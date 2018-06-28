#!/usr/bin/env python
from __future__ import division
from argparse import ArgumentParser
from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD
from genologics.entities import Process , Workflow, Stage, Artifact
from xml.dom.minidom import parseString
import logging
import sys
import glsapiutil
import platform
import xml.etree.ElementTree as ET

HOSTNAME = platform.node()
VERSION = 'v2'
APIURI = BASEURI + '/api/' + VERSION + '/'

api = glsapiutil.glsapiutil2()
api.setHostname( 'http://'+HOSTNAME ) ##api only seems to work with http, not https. Find out why, and how this should be done.
api.setVersion( VERSION )
api.setup( USERNAME, PASSWORD )


DESC = """
Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""


class PassSamples():

    def __init__(self, process):
        self.process = process
        self.out_arts = []
        self.rerun_samples = {}
        self.continue_arts = []
        self.current_WF = self._get_current_WF() 
        self.rerun_step =  ['CG002 - Sort HiSeq X Samples (HiSeq X)', 'CG002 - Sort HiSeq Samples']
        self.rerun_stage = self._get_next_step_stage_URI(self.rerun_step)
        #self.continue_stage = self._get_next_step_stage_URI(['CG002 - Delivery'])
        self.warning_duplicate_samples = []
        self.rXML = []
        self.abstract = ''
        self.remove_from_WF = []

    def get_artifacts(self):
        for art in self.process.all_outputs(unique=True):
            if art.type == 'Analyte':
                self.out_arts.append(art)
                try:
                    rerun = art.udf['Rerun']
                except:
                    rerun = False
                if rerun:
                    self._get_rerun_arts(art)
                else:
                    self.continue_arts.append(art)

    def _get_rerun_arts(self, art):
        all_arts_in_sort=[]
        for sample in art.samples:
            sample_id = sample.id
            out_arts = lims.get_artifacts(samplelimsid = sample_id,
                            process_type = self.rerun_step)
            all_arts_in_sort += out_arts
        correct_process=None
        for art in all_arts_in_sort:
            if correct_process:
                if art.parent_process.date_run > correct_process.date_run:
                    correct_process = art.parent_process
            else:
                correct_process = art.parent_process
        for art  in all_arts_in_sort:
            if art.parent_process == correct_process:
                art_sample_key = [s.id for s in art.samples]
                art_sample_key = '_'.join(list(set(art_sample_key)))
                self.rerun_samples[art_sample_key] = {'art' : art, 'next_step_stage' : self.rerun_stage}
        print self.rerun_samples

    def check_same_sample_in_many_rerun_pools(self):
        all_samples = []
        for s in self.rerun_samples.keys():
            all_samples += s.split('_')
        for s in set(all_samples):
            all_samples.remove(s)
        self.warning_duplicate_samples = list(set(all_samples))

    def get_arts_to_remove(self):
        samples = []
        for key, art in self.rerun_samples.items():
            print 'hlkjhlkjhlkjhkl'
            samples+=[s.id for s in art['art'].samples]
        samples=list(set(samples))
        for art in self.process.all_inputs():
            for samp in art.samples:
                if samp.id in samples:
                    print art
                    self.remove_from_WF.append(art)
        self.remove_from_WF=list(set(self.remove_from_WF))           
        print self.remove_from_WF 


    def _get_current_WF(self):
        art = self.process.all_inputs()[0]
        art_XML = api.GET(APIURI + 'artifacts/' + art.id)
        art_dom = parseString( art_XML )
        WF_node = art_dom.getElementsByTagName('workflow-stage')[-1]
        wf_id = WF_node.getAttribute('uri').split('/stages/')[0].split('/')[-1]
        try:
            print 'WF'
            print Workflow(lims,id = wf_id)
            return Workflow(lims,id = wf_id)
        except:
            sys.exit('Could not get the current Work Flow. Contact lims developer.')

    def _get_next_step_stage_URI(self, next_step):
        for stage in self.current_WF.stages:
            print stage.name
            if stage.name in next_step:
                return stage.uri
        sys.exit('Could not get the next step Stage. Contact lims developer.')

    def assign_arts(self):
        for key, art in self.rerun_samples.items():
            self.make_assig_xml(art['art'].uri, art['next_step_stage'])
        #for art in self.continue_arts:
        #    self.make_assig_xml(art.uri, )

    def make_assig_xml(self, art_uri, next_step_uri):
        self.rXML.append( '<assign stage-uri="' + next_step_uri + '">' )
        self.rXML.append( '<artifact uri="' + art_uri + '"/>' )
        self.rXML.append( '</assign>' )

    def remove_arts(self):
        for art in self.remove_from_WF:
            self.rXML.append( '<unassign workflow-uri="' + self.current_WF.uri + '">' )
            self.rXML.append( '<artifact uri="' + art.uri + '"/>' )
            self.rXML.append( '</unassign>' )

    def rout(self):
        routeXML = "".join( self.rXML )
        if len(routeXML) > 0:
            routeXML = '<rt:routing xmlns:rt="http://genologics.com/ri/routing">' + routeXML + '</rt:routing>'
            responseXML = api.POST( routeXML, APIURI + "route/artifacts/" )
            if 'exception' in responseXML:
                sys.exit('XML routing error. Contact Lims Developer. '+responseXML)

def main(lims, args):
    process = Process(lims, id = args.pid)
    PS = PassSamples(process)
    PS.get_artifacts()
    PS.check_same_sample_in_many_rerun_pools()
    PS.get_arts_to_remove()
    PS.assign_arts()
    PS.remove_arts()
    PS.rout()

    abstract = 'Probably no errors. Maybe passed '+str(len(PS.rerun_samples.keys()))+' arts for rerun.'
    #if PS.warning_duplicate_samples......

    #if PS.remove_from_WF:
    #    abstract += ' Probably removed ' + str(len(PS.remove_from_WF))+ ' artifacts from the wf.'

    print >> sys.stderr, abstract ## How do "flush this message in a correct way?"

if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid',
                        help='Lims id for current Process')
    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args)

