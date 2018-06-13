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

HOSTNAME = platform.node()
VERSION = 'v2'
APIURI = BASEURI + '/api/' + VERSION + '/'

api = glsapiutil.glsapiutil2()
api.setHostname( 'http://'+HOSTNAME ) ##api only seems to work with http, not https. Find out why, and how this should be done.
api.setVersion( VERSION )
api.setup( USERNAME, PASSWORD )


DESC = """
Script to pass samples and pools to next step. Sort of specific script:

Single arts                                 --> Next Step
RML-Pools                                   --> Next Step
Non RML-Pools --> split in uniq sample arts --> Next Step

Uniq sample arts are derived by 
    1.  geting the sample list of the pool
    2.  picking the input artifact to the Reception Control step, for 
        each sample in the list. This assuems the inputs will be one per 
        sample, wich is allways true since the Reception Control step is 
        the first step of any WF.

Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""


class PassSamples():

    def __init__(self, process):
        self.process = process
        self.input_arts = self.process.all_inputs(unique=True)
        self.remove_from_WF = []
        self.send_to_next_step = []
        self.next_step = 'CG002 - Sequence Aggregation'
        self.current_WF = ''
        self.next_step_stage = ''
        self.rXML = []
        self.uniq_artifacts = {}
        self.abstract = ''

    def get_artifacts(self):
        for art in self.input_arts:
            if art.samples[0].udf['Sequencing Analysis'][0:3]=='RML' or len(art.samples)==1:
                ## this is a sample or a RML and will be passed to next step
                self.send_to_next_step.append(art)  
                print 'pass'
                print art.id
            else:
                ## this is a pool and we want to pass its samples to next step
                print 'split'
                print art.id
                self._get_individual_artifacts(art)
                self.remove_from_WF.append(art)
        print self.uniq_artifacts
        self.send_to_next_step += self.uniq_artifacts.values()
        self.send_to_next_step = list(set(self.send_to_next_step))

    def _get_individual_artifacts_(self, pool):
        for sample in pool.samples: 
            sample_id = sample.id
            ## get anyone - there are result files
            out_art = lims.get_artifacts(samplelimsid = sample_id, process_type = ['CG002 - Reception Control','CG002 - Reception Control (Dev)'])[0]
            ## get in_arts - these are analytes
            for a in out_art.input_artifact_list():
                if a.samples[0].id==sample_id:
                    art=a
                    break
            if not art:
                sys.exit('Pool '+pool+' did not go through CG002 - Reception Control. Contact lims developer.')
            if sample_id in self.uniq_artifacts.keys():
                ## if the same sample occured in sevaral pools in the process, make sure we are piking only
                ## one artifact, and the right one, for that sample:
                if self.uniq_artifacts[sample_id].parent_process.date_run < art.parent_process.date_run:
                    self.uniq_artifacts[sample_id] = art
            else:
                self.uniq_artifacts[sample_id] = art

    def _get_individual_artifacts(self, pool):
        ## Assuming first artifact is allways named sample.id + 'PA1. Not sure if true. Need to check
        for sample in pool.samples:
            sample_id = sample.id
            first_sample_artifact = Artifact(lims, id = sample.id + 'PA1')
            self.uniq_artifacts[sample_id] = first_sample_artifact

    def get_current_WF(self):
        # This should be done in a better way...
        # pick any art from the current wf:
        art = self.input_arts[0]
        art_XML = api.GET(APIURI + 'artifacts/' + art.id)
        art_dom = parseString( art_XML )
        # look for the last "workflow-stage" node, since that's
        # where we currently are
        WF_node = art_dom.getElementsByTagName('workflow-stage')[-1]
        wf_id = WF_node.getAttribute('uri').split('/stages/')[0].split('/')[-1]
        self.current_WF = Workflow(lims,id = wf_id)
        if not self.current_WF:
            sys.exit('Could not get the current Work Flow. Contact lims developer.')

    def get_next_step_stage_URI(self):
        for stage in self.current_WF.stages:
            if stage.name == self.next_step:
                self.next_step_stage = stage.uri
                break
        if not self.next_step_stage:
            sys.exit('Could not get the current Work Flow Stage. Contact lims developer.')

    def assign_arts(self):
        for art in self.send_to_next_step:
            #newURI = art.uri[ : art.uri.rfind('?state') ]
            self.rXML.append( '<assign stage-uri="' + self.next_step_stage + '">' ) 
            self.rXML.append( '<artifact uri="' + art.uri + '"/>' )#### KANSKE newURI IST F art.uri
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
            responseXML = api.POST( routeXML, APIURI + "route/artifacts/" )##how catch fail? Ask ciara.
            logging.debug( responseXML )
            self.passed=True        
            


def main(lims, args):
    process = Process(lims, id = args.pid)
    PS = PassSamples(process)
    PS.get_artifacts()
    PS.get_current_WF()
    PS.get_next_step_stage_URI()
    PS.assign_arts()
    PS.remove_arts()
    PS.rout()

    if PS.passed:
        abstract = 'Probably no errors. Maybe passed '+str(len(PS.send_to_next_step))+' arts to next step.'
        if PS.remove_from_WF:
            abstract += ' Probably removed ' + str(len(PS.remove_from_WF))+ ' artifacts from the wf.'
        print >> sys.stderr,abstract ## How do "flush this message in a correct way?"
    else:
        print >> sys.exit('FAIL') 
  

if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid',
                        help='Lims id for current Process')
    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args)
