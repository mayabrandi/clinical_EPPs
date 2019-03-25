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

import sys

class BufferVolume():
    def __init__(self, process):
        self.process = process
        self.artifacts = []
        self.passed_arts = 0
        self.failed_arts = 0
        self.missing_udfs = False
        self.high_volume = []
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
            concentration = None 
        return concentration

    def apply_calculations(self):
        for artifact in self.artifacts:
            concentration = self.check_udfs(artifact)
            if concentration and (concentration <= self.final_concentration):
                artifact.udf['Volume Buffer (ul)'] = 0
                artifact.udf['Sample Volume (ul)'] = 10
                self.passed_arts +=1
            elif concentration and (concentration > self.final_concentration):
                samp_vol = 5
                total_volume = (concentration*samp_vol)/self.final_concentration
                eb_volume = total_volume - samp_vol
                if eb_volume > 150:
                    self.high_volume.append(artifact.samples[0].name) #samples will always be a list of only one value
                    artifact.qc_flag = False
                elif eb_volume < 2:
                    eb_volume = 2.0
                    samp_vol = eb_volume/((concentration/self.final_concentration)-1)
                    total_volume = eb_volume + samp_vol
                    if samp_vol > 20:
                        self.high_volume.append(artifact.samples[0].name)
                        artifact.qc_flag = False

                artifact.udf['Total Volume (uL)'] = total_volume
                artifact.udf['Volume Buffer (ul)'] = eb_volume
                artifact.udf['Sample Volume (ul)'] = samp_vol  
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
    elif BV.high_volume:
        abstract = "Samples: " + ', '.join(BV.high_volume) + ", had over 180 ul EB volume. Or over 20 ul Sample Volume " + abstract
        sys.exit(abstract)
    else:
        print >> sys.stderr, abstract


if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid',
                        help='Lims id for current Process')
    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()

    main(lims, args)
