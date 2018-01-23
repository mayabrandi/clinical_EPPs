#!/usr/bin/env python
# -*- coding: utf-8 -*-

from optparse import OptionParser
import glsapiutil
from xml.dom.minidom import parseString
import sys
DEBUG = False
#####################################################################################
### In this example, the output artifacts could be routed to one or both of these two potential WF/stage combinations
### Configuration is required --- need to create artifact UDFs which will be the checkboxes we examine
### For this ex, UDF names "For HiSeq2500" need to checkbox UDFs configured in LIMS under analyte

HiSeq2500 = {   'WF' : 'CG003 SureSelect XT',
                'Stage' : 'CG002 - Aliquot Samples for Library Pooling',
                'UDF' : "HiSeq2500"
            }

HiSeqX = {      'WF' : 'CG003 WGS PCR free',
                'Stage' : 'CG002 - Sort HiSeq X Samples (HiSeq X)',
                'UDF' : "HiseqX"
                }


skip_norm = {   'WF' : 'CG001 Microbial WGS',
                'Stage' : 'CG002 - Sort HiSeq X Samples (HiSeq X)',
                'UDF' : "Skip Normalization"
                }


availableStages = [ HiSeq2500, HiSeqX, skip_norm]
# Add more stages by adding to this list.

#####################################################################################

def getStageURI( wfName, stageName ):

    response = ""

    wURI = api.getBaseURI() + "configuration/workflows"
    wXML = api.GET( wURI )
    wDOM = parseString( wXML )

    workflows = wDOM.getElementsByTagName( "workflow" )
    for wf in workflows:
        name = wf.getAttribute( "name" )
        if name == wfName:
            wfURI = wf.getAttribute( "uri" )
            wfXML = api.GET( wfURI )
            wfDOM = parseString( wfXML )
            stages = wfDOM.getElementsByTagName( "stage" )
            for stage in stages:
                stagename = stage.getAttribute( "name" )
                if stagename == stageName:
                    response = stage.getAttribute( "uri" )
                    break
            break
    return response

def routeAnalytes( stageURIlist, input_art ):

    ANALYTES = []		### Cache, prevents unnessesary GET calls

    artifacts_to_route = {}
    for stageURI in stageURIlist:
        artifacts_to_route[ stageURI ] = []

    ## Step 1: Get the step XML
    processURI = args.stepURI + "/details"
    processXML = api.GET( processURI )
    processDOM = parseString( processXML )

    ## Step 2: Cache Output Analytes
    if input_art:
        analytes = processDOM.getElementsByTagName( "input" )
    else:
        analytes = processDOM.getElementsByTagName( "output" )
    for analyte in analytes:
        if input_art or analyte.getAttribute( "type" ) == "Analyte":
            analyteURI = analyte.getAttribute( "uri" )
            if analyteURI in ANALYTES:
                pass
            else:
                ANALYTES.append( analyteURI )
                analyteXML = api.GET( analyteURI )
                analyteDOM = parseString( analyteXML )

                ## Step 3: Add the analytes to the list of ones to be routed
                for stage in range(len(availableStages)):
                    if api.getUDF( analyteDOM , availableStages[stage]["UDF"] ) == 'true':
                        artifacts_to_route[ stageURIlist[stage] ].append( analyteURI )

    if DEBUG: print artifacts_to_route

    def pack_and_send( stageURI, a_ToGo ):
        ## Step 4: Build and submit the routing message
        rXML = '<rt:routing xmlns:rt="http://genologics.com/ri/routing">'
        rXML = rXML + '<assign stage-uri="' + stageURI + '">'
        for uri in a_ToGo:
            rXML = rXML + '<artifact uri="' + uri + '"/>'
        rXML = rXML + '</assign>'
        rXML = rXML + '</rt:routing>'
        response = api.POST( rXML, api.getBaseURI() + "route/artifacts/" )
        return response

    # Sends seperate routing messages for each stage
    for stage, artifacts in artifacts_to_route.items():

        r = pack_and_send( stage, artifacts )

        if DEBUG: print r
        if len( parseString( r ).getElementsByTagName( "rt:routing" ) ) > 0:
            msg = str( len(artifacts) ) + " samples were added to the " + stage + " step. "
        else:
            msg = r
        print msg

    #status = "OK"
    #api.reportScriptStatus( args.stepURI, status, msg )

def setupArguments():

    Parser = OptionParser()
    Parser.add_option('-u', "--username", action='store', dest='username')
    Parser.add_option('-p', "--password", action='store', dest='password')
    Parser.add_option('-s', "--stepURI", action='store', dest='stepURI')
    Parser.add_option("-i", action='store_true', dest='input',
                        help=("Use this tag if you run the script from a QC step."))

    return Parser.parse_args()[0]

def main():

    global args
    args = setupArguments()

    global api
    api = glsapiutil.glsapiutil2()
    api.setURI( args.stepURI )
    api.setup( args.username, args.password )

    stageURIlist = [ getStageURI( stage["WF"], stage["Stage"] ) for stage in availableStages ]

    if DEBUG: print stageURIlist

    if "" in stageURIlist:
        print "Could not retrieve the workflow / stage combination"
        print stageURIlist

    routeAnalytes( stageURIlist , args.input)

if __name__ == "__main__":
    main()
