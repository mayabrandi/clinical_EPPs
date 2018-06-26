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
        self.rerun_step =  ['CG002 - Sort HiSeq X Samples (HiSeq X)', 'CG002 - Sort HiSeq Samples']
        self.continue_step =  'CG002 - Delivery'
        self.current_WF = ''
        self.rXML = []
        self.abstract = ''

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

    def _get_rerun_arts(self, art):
        next_step_stage = self._get_next_step_stage_URI()
        all_arts_in_sort=[]
        for sample in art.samples:
            sample_id = sample.id
            out_arts = lims.get_artifacts(samplelimsid = sample_id,
                            process_type = self.rerun_step)
            all_arts_in_sort += out_arts 
        for art  in all_arts_in_sort:
            art_sample_key = [s.id for s in art.samples]
            art_sample_key = '_'.join(list(set(art_sample_key)))
            self.rerun_samples[art_sample_key] = {'art' : art, 'next_step_stage' : next_step_stage}

    def get_current_WF(self):
        art = self.process.all_inputs()[0]
        art_XML = api.GET(APIURI + 'artifacts/' + art.id)
        art_dom = parseString( art_XML )
        WF_node = art_dom.getElementsByTagName('workflow-stage')[-1]
        wf_id = WF_node.getAttribute('uri').split('/stages/')[0].split('/')[-1]
        self.current_WF = Workflow(lims,id = wf_id)
        if not self.current_WF:
            sys.exit('Could not get the current Work Flow. Contact lims developer.')

    def _get_next_step_stage_URI(self):
        for stage in self.current_WF.stages:
            if stage.name in self.rerun_step:
                return stage.uri
        sys.exit('Could not get the next step Stage. Contact lims developer.')

    def assign_arts(self):
        for key, art in self.rerun_samples.items():
            self.rXML.append( '<assign stage-uri="' + art['next_step_stage'] + '">' )
            self.rXML.append( '<artifact uri="' + art['art'].uri + '"/>' )
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
    PS.get_current_WF()
    PS.get_artifacts()
    PS.assign_arts()
   # PS.remove_arts()
    PS.rout()

    abstract = 'Probably no errors. Maybe passed '+str(len(PS.rerun_samples.keys()))+' arts for rerun.'
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

