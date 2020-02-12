#!/home/glsai/miniconda2/envs/epp_master/bin/python
DESC="""EPP script to calculate sample volume and EB volume from concentration and volume
udf:s in Clarity LIMS.
Maya Brandi
"""
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process
import sys

class BufferVolume():
    def __init__(self, process):
        self.process = process
        self.artifacts = []
        self.passed_arts = 0
        self.failed_arts = 0
        self.missing_udfs = False
        self.buffer_out_of_range = []
        self.final_concentration = float(process.udf['Final Concentration (ng/ul)'])

    def get_artifacts(self):
        all_artifacts = self.process.all_outputs(unique=True)
        self.artifacts = filter(lambda a: a.output_type == "Analyte", all_artifacts)

    def apply_calculations(self):
        for artifact in self.artifacts:
            concentration = artifact.udf.get('Concentration')
            if not concentration:
                self.missing_udfs = True
                self.failed_arts +=1
                continue
            artifact.qc_flag = 'PASSED'
            if concentration <= self.final_concentration:
                samp_vol = 15
                buffer_volume = 0
            else:
                samp_vol = 4
                buffer_volume = float(concentration*samp_vol)/self.final_concentration - samp_vol
                if not 2 < buffer_volume < 180:
                    self.buffer_out_of_range.append(artifact.samples[0].name)
                    artifact.qc_flag = 'FAILED'
            self.passed_arts +=1
            artifact.udf['Total Volume (uL)'] = buffer_volume + samp_vol
            artifact.udf['Volume Buffer (ul)'] = buffer_volume
            artifact.udf['Sample Volume (ul)'] = samp_vol
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
        sys.exit('Could not apply calculations for all samples. "Final Concentration (ng/ul)" and "Concentration" must be set.')
    elif BV.failed_arts:
        sys.exit(abstract)
    elif BV.buffer_out_of_range:
        abstract = abstract+" Samples: " + ', '.join(BV.buffer_out_of_range) + ", got a high or low Buffer Volume."
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
