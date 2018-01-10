#!/home/glsai/miniconda2/envs/epp_master/bin/python
DESC="""EPP script to calculate sample volume and EB volume from concentration and volume
udf:s in Clarity LIMS.
Maya Brandi
"""
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process
from genologics.epp import EppLogger

import logging
import sys

class BufferVolume():
    def __init__(self, process):
        self.process = process
        self.artifacts = []
        self.passed_arts = 0
        self.failed_arts = 0
        self.missing_udfs = False
        self.high_total_volume = []
        self.final_concentration = float(process.udf['Final Concentration (nM)'])

    def get_artifacts(self):
        all_artifacts = self.process.all_outputs(unique=True)
        self.artifacts = filter(lambda a: a.output_type == "Analyte", all_artifacts)

    def check_udfs(self, artifact):
        try:
            #amount_needed = float(artifact.udf['Amount needed (ng)'])
            concentration = float(artifact.udf['Concentration (nM)'])
        except:
            #amount_needed = None
            self.missing_udfs = True
        return concentration

    def apply_calculations(self):
        for artifact in self.artifacts:
            concentration = self.check_udfs(artifact)
            samp_vol = 5
            artifact.udf['Sample Volume (ul)'] = samp_vol
            if concentration <= self.final_concentration:
                artifact.udf['Volume Buffer (ul)'] = 0
                self.passed_arts +=1
            elif concentration > self.final_concentration:
                total_volume = (concentration*samp_vol)/self.final_concentration
                eb_volume = total_volume - samp_vol
                artifact.udf['Volume Buffer (ul)'] = eb_volume
                self.passed_arts +=1
                artifact.udf['Total Volume (uL)'] = total_volume
                if eb_volume > 180:
                    self.high_total_volume.append(artifact.samples[0].name) #samples will always be a list of only one value
            else:
                self.failed_arts +=1
            artifact.put()

def main(lims,args):
    process = Process(lims,id = args.pid)
    BV = BufferVolume(process)
    BV.get_artifacts()
    BV.apply_calculations()

    d = {'ca': BV.passed_arts,
         'ia': BV.failed_arts}

    abstract = ("Updated {ca} artifact(s), skipped {ia} artifact(s) with "
                "wrong and/or blank values for some udfs. ").format(**d)

    if BV.missing_udfs:
        sys.exit('Could not apply calculations for all samples. "Final Concentration (nM)" and "Concentration (nM)" must be set.')
    elif BV.failed_arts:
        sys.exit(abstract)
    elif BV.high_total_volume:
        abstract = "Samples: " + ', '.join(BV.high_total_volume) + ", had over 180 ul total volume. " + abstract
        sys.exit(abstract)
    else:
        print >> sys.stderr, abstract


if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid',
                        help='Lims id for current Process')
    parser.add_argument('--log',
                        help='Log file for runtime info and errors.')
    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()

    main(lims, args)
