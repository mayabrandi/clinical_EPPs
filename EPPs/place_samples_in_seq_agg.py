#!/usr/bin/env python
from __future__ import division
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD
from genologics.entities import Process
from genologics.epp import EppLogger


from xml.dom.minidom import parseString
from collections import namedtuple
import string
from datetime import date

from art_hist import make_hist_dict_no_stop
import logging
import sys

import glsapiutil
import platform

###### clean up:
HOSTNAME = platform.node()
VERSION = 'v2'
api = glsapiutil.glsapiutil2()

api.setHostname( 'http://'+HOSTNAME ) ##api only seems to work with http, not https. Find out why, and how this should be done.
api.setVersion( VERSION )
api.setup( USERNAME, PASSWORD )

BASE_URI = BASEURI + '/api/' + VERSION + '/'
##############


DESC = """

Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""


class PassSamples():

    def __init__(self, process):
        self.process = process
        self.remove_from_WF = []
        self.send_to_SeqAgg = []
        self.stop_step = 'CG002 - Reception Control'
        self.next_step = 'CG002 - Sequence Aggregation'
        self.current_WF = ''
        self.current_WF_stage = ''
        self.rXML = []
        self.uniq_artifacts = {}

    def get_artifacts(self):
        all_artifacts = self.process.all_inputs(unique=True)
        arts = filter(lambda a: a.output_type == "Analyte" , all_artifacts)
        for art in arts:
            if art.samples[0].udf['customer']=='cust001' or len(art.samples)==1:
                self.send_to_SeqAgg.append(art)
            else:
                ## this is a pool and we want to pass its samples to seq agg
                self._get_individual_artifacts(art)
                self.remove_from_WF.append(art)
        self.send_to_SeqAgg += self.uniq_artifacts.values()
        self.send_to_SeqAgg = list(set(self.send_to_SeqAgg))

    def _get_individual_artifacts(self, pool):
        for sample in pool.samples:
            sample_id = sample.id
            ## there will only be one art per sample in the reception control step:
            out_art = lims.get_artifacts(samplelimsid = sample_id, process_type = self.stop_step)[0]
            art = out_art.input_artifact_list()[0]
            if sample_id in self.uniq_artifacts.keys():
                ## if the same sample occured in sevaral pools in the process, make sure we are piking only
                ## one, and the right one, artifact for that sample:
                if self.uniq_artifacts[sample_id].parent_process.date_run < art.parent_process.date_run:
                    self.uniq_artifacts[sample_id] = art
            else:
                self.uniq_artifacts[sample_id] = art

    def get_current_WF(self):
        # pick any art from the current wf:
        art = self.remove_from_WF[0]
        art_XML = api.GET(BASE_URI + 'artifacts/' + art.id)
        art_dom = parseString( art_XML )
        # look for the last "workflow-stage" node, since that's
        # where we currently are
        WF_node = art_dom.getElementsByTagName('workflow-stage')[-1]
        self.current_WF = WF_node.getAttribute('uri').split('/stages/')[0]

    def get_stage_URI(self):
        # pick any art from the current wf:
        art = self.remove_from_WF[0]
        for i in art.workflow_stages_and_statuses:
            stage_uri = i[0]._uri
            stage_name = i[2]
            if stage_name == self.next_step:
                self.current_WF_stage = stage_uri
                break

    def assign_arts(self):
        for art in self.send_to_SeqAgg:
            newURI = art.uri[ : art.uri.rfind('?state') ]
            self.rXML.append( '<assign stage-uri="' + self.current_WF_stage + '">' ) ### om ej funkar anv bestURI=self.getStageURI(self.current_WF , 'CG002 - Sequence Aggregation')
            self.rXML.append( '<artifact uri="' + art.uri + '"/>' )#### KANSKE newURI IST F art.uri
            self.rXML.append( '</assign>' )

    def remove_arts(self):
        for art in self.remove_from_WF:
            self.rXML.append( '<unassign workflow-uri="' + self.current_WF + '">' )
            self.rXML.append( '<artifact uri="' + art.uri + '"/>' )
            self.rXML.append( '</unassign>' )

    def rout(self):
        routeXML = "".join( self.rXML )
        if len(routeXML) > 0:
            routeXML = '<rt:routing xmlns:rt="http://genologics.com/ri/routing">' + routeXML + '</rt:routing>'
            responseXML = api.POST( routeXML, BASE_URI + "route/artifacts/" )
            logging.debug( responseXML )


    def getStageURI( self,wURI, stageUDFValue ):
        # get the stageURI for the closest matching stage 
        #similar to workflow
        response = ""
        wXML = api.GET( wURI )
        wDOM = parseString( wXML )
        #logging.debug( wXML )
        stages = wDOM.getElementsByTagName( "stage" )
        words = stageUDFValue.lower().split( " " )
        #logging.debug ( words )
        candidateURIs = []
        for stage in stages:
            found = 0
            stagename = stage.getAttribute( "name" ).lower()
            #logging.debug ( stagename )
            for word in words:
                if word in stagename:
                    found += 1
            if found == len(words):
                # we have a candidate!
                candidateURIs.append( stage.getAttribute( "uri" ) )
        if len( candidateURIs ) == 1:
            return candidateURIs[0]
        else:
            #logging.debug( candidateURIs )
            return ""



def main(lims, args):
    process = Process(lims, id = args.pid)
    PS = PassSamples(process)
    PS.get_artifacts()
    PS.get_current_WF()
    PS.get_stage_URI()
    PS.assign_arts()
    PS.remove_arts()
    PS.rout()

if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid',
                        help='Lims id for current Process')
    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args)
