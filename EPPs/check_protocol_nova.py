#!/usr/bin/env python
from __future__ import division
from argparse import ArgumentParser
from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process
import sys

DESC = """The script is taylored for the Make Pool steps in the NovaSeq WF. Same script
for both Xp and Standard. It will check we are in the correct step based on the 
'Flowcell Type' and 'Protocol type' udfs selected in the parrent process.

It will allso set the denatudation volumes for Standard samples. Not for Xp.

Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""

class CheckNovaSettings():

    def __init__(self, process):
        self.process = process
        self.artifacts = []
        self.standard = 'Make Bulk Pool for NovaSeq Standard (NovaSeq 6000 v2.0)'
        self.xp = 'Make Bulk Pool for NovaSeq Xp (NovaSeq 6000 v2.0)'
        self.parent_process = process.all_inputs()[0].parent_process
        self.flowcell_type = self.parent_process.udf.get('Flowcell Type') 
        self.protocol_type = self.parent_process.udf.get('Protocol type')
        self.denaturation_volumes =  {'S1': {'Volume of Pool to Denature (ul)': 100.0,
                                                    'NaOH Volume (ul)' : 25.0,
                                                    'Tris-HCl Volume (ul)': 25.0} , 
                                      'S2': {'Volume of Pool to Denature (ul)': 150.0,
                                                    'NaOH Volume (ul)' : 37.5,
                                                    'Tris-HCl Volume (ul)': 37.5},
                                      'S4': {'Volume of Pool to Denature (ul)': 310,
                                                    'NaOH Volume (ul)' : 77.5,
                                                    'Tris-HCl Volume (ul)': 77.5}}

    def get_artifacts(self):
        """Get output artifacts"""

        all_artifacts = self.process.all_outputs(unique=True)
        self.artifacts = filter(lambda a: a.output_type == "Analyte" , all_artifacts)

    def check_protocol_setings(self):
        """Will exit with warning if wrong protocol type"""
        if self.protocol_type == 'NovaSeq Standard' and self.process.type.name != self.standard:
            sys.exit('Wrong protocol type')
        elif self.protocol_type == 'NovaSeq Xp' and self.process.type.name != self.xp:
            sys.exit('Wrong protocol type')

    def set_volumes_for_standard(self):
        """Sets the denatudation volumes for Standard samples."""        

        if self.protocol_type == 'NovaSeq Standard':
            for key, val in self.denaturation_volumes[self.flowcell_type].items():
                self.process.udf[key] = val
            self.process.put()
      
    def set_udfs(self):
        """Sets 'Flowcell Type' and 'Loading Workflow Type' on the artifacts. Needed in next step."""

        for art in self.artifacts:
            art.udf['Flowcell Type'] = self.flowcell_type
            art.udf['Loading Workflow Type'] = self.protocol_type
            art.put()

def main(lims, args):
    process = Process(lims, id = args.pid)
    CNS = CheckNovaSettings(process)
    CNS.get_artifacts()
    CNS.check_protocol_setings()
    CNS.set_volumes_for_standard()
    CNS.set_udfs()


if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid',
                        help='Lims id for current Process')
    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args)
