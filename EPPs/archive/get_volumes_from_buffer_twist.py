#!/usr/bin/env python
from __future__ import division
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process
from genologics.epp import EppLogger

import sys
import os

DESC = """Getting Volume Elution from previous step of type defined by process_types.
    If volume found, setting the value Volume udf on artifact of current step."""

def get_buffer(art, process_types):
    '''Getting Volume Elution from previous step of type defined by process_types.
    If volume found, setting the value Volume udf on artifact of current step.'''

    sample = art.samples[0]
    buffer_arts = lims.get_artifacts(samplelimsid = sample.id, process_type = process_types)
    volume_buffer = None
    for buffer_art in buffer_arts:
        if buffer_art.parent_process.date_run < buffer_arts[0].parent_process.date_run:
            continue
        if buffer_art.udf.get('Volume Elution (ul)'):
            volume_buffer = buffer_art.udf.get('Volume Elution (ul)')
    if volume_buffer is not None:
        art.udf['Volume (ul)'] = volume_buffer
        art.put()
        return 1
    else:
        return 0


def main(lims, args):
    process = Process(lims, id = args.pid)
    artifacts = process.all_outputs()
    updated_arts = 0
    for art in artifacts:
        updated_arts += get_buffer(art, args.process_types)

    print >> sys.stderr, 'Updated '+str(updated_arts)+' samples with volume from Buffer step.'

if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('-p', dest = 'pid',
                        help='Lims id for current Process')
    parser.add_argument('-s', dest = 'process_types',  nargs='+', 
                        help='Get buffer from this process type(s)')

    args = parser.parse_args()
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args)

