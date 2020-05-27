#!/home/glsai/miniconda2/envs/epp_master/bin/python
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process

import csv
import sys

DESC = """epp script to generate Bravo CSV file
Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""


class ToCSV():

    def __init__(self, process, amount_step):
        self.process = process
        self.plate_dict = {}
        self.failed_samples = []
        self.amount_step=amount_step
        self.translate_amount = {10: {'Ligation Master Mix':'B', 'PCR Plate': 'Plate 3'},
                                 50: {'Ligation Master Mix':'A', 'PCR Plate': 'Plate 2'},
                                 250: {'Ligation Master Mix':'A', 'PCR Plate': 'Plate 1'}}

    def get_artifacts(self):
        all_artifacts = self.process.all_outputs(unique=True)
        self.artifacts = filter(lambda a: a.output_type == "Analyte" , all_artifacts)

    def get_amount(self, sample_id):
        amount_arts = lims.get_artifacts(process_type=self.amount_step, samplelimsid=sample_id)
        amount_art = amount_arts[0]
        for art in amount_arts:
            if art.output_type != "Analyte":
                continue
            if art.parent_process.date_run >= amount_art.parent_process.date_run:
                amount_art = art
        return amount_art.udf.get('Amount (ng)')
            

    def make_file(self, hamilton_file):
        hamilton_file = hamilton_file + '_'+'KAPA_Hamilton.txt'
        hamilton_csv = open( hamilton_file , 'wb')
        wr = csv.writer(hamilton_csv)
        wr.writerow(['LIMS ID', 'Sample Well', 'Ligation Master Mix', 'Index Well', 'PCR Plate'])
        for art in self.artifacts:
            sample = art.samples[0].id
            well = art.location[1].replace(':','')
            amount = self.get_amount(sample)
            if amount<=10:
                amount=10
            mix_plate = self.translate_amount.get(amount)
            if mix_plate:
                row_list = [sample ,well ,mix_plate['Ligation Master Mix'],'-' ,mix_plate['PCR Plate']]
                wr.writerow(row_list)
            else:
                self.failed_samples.append(sample)

def main(lims, args):
    process = Process(lims, id = args.pid)
    TCSV = ToCSV(process, args.amount_step)
    TCSV.get_artifacts()
    TCSV.make_file(args.hamilton_file)

    if TCSV.failed_samples:
        abstract = 'samples missed amount data: '+ ', '.join(TCSV.failed_samples)
    else:
        abstract = "Bravo CSV sucsessfully generated."
    print >> sys.stderr, abstract


if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid',
                        help='Lims id for current Process')
    parser.add_argument('--hamilton_file',
                        help=('file'))
    parser.add_argument('--amount_step',
                        help=('amount step name'))
    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args)
