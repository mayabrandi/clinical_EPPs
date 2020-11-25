#!/home/glsai/miniconda2/envs/epp_master/bin/python
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI, USERNAME, PASSWORD
from genologics.entities import Process

from datetime import date

import sys

DESC = """

Written by Maya Brandi, Science for Life Laboratory, Stockholm, Sweden
"""


class SamplePlacementMap():

    def __init__(self, process):
        self.artifacts = [a for a in process.all_outputs() if a.type == 'Analyte']
        self.process = process
        self.container_dict = {}

    def _make_source_container_dict(self):
        for out_art in self.artifacts:
            art = out_art.input_artifact_list()[0]
            source_well = art.location[1]
            source_cont = art.location[0]
            if not source_cont in self.container_dict:
                self.container_dict[source_cont] = {'table': [], 'visual_map': {}}
            self.container_dict[source_cont]['table'].append((source_well, art, out_art))
            self.container_dict[source_cont]['visual_map'][source_well] = (art, out_art)

    def make_html(self, resultfile):
        ### HEADER ###
        html = []
        html.append(
            '<html><head><style>table, th, td {border: 1px solid black; border-collapse: collapse;}</style><meta content="text/html; charset=UTF-8" http-equiv="Content-Type"><link href="../css/g/queue-print.css" rel="stylesheet" type="text/css" media="screen,print"><title>')
        html.append('Placement Map for lane:' + self.process.udf.get('Lane', ''))
        html.append(self.process.udf.get('Protocol type') + ' ' + self.process.udf.get('Flowcell Type'))
        html.append('</title></head>')
        html.append('<body><div id="header"><h1 class="title">')
        html.append('Placement Map for lane: ' + self.process.udf.get('Lane', '') + '<br>')
        html.append(self.process.udf.get('Protocol type') + ' ' + self.process.udf.get('Flowcell Type'))
        html.append('</h1></div>')
        html.append('Created by: ' + USERNAME + ', ' + str(date.today().isoformat()))
        self._make_source_container_dict()
        for container, info in self.container_dict.items():
            table_info = info['table']
            visual_map = info['visual_map']
            table_info.sort()
            # Data about this specific container
            html.append(
                '<table class="group-contents"><br><br><thead><tr><th class="group-header" colspan="10"><h2>Source Plate: ' + container.name + ' (' + container.id + ')')
            html.append('</h2>')

            ## Columns Header
            html.append(
                '<tr><th style="width: 7%;" class="">Sample ID/Pool Name (if RML)</th><th style="width: 7%;" class="">Well</th><th style="width: 7%;" class="">Adjuster Per Sample Volume (ul)</th></tr></thead>')
            html.append('<tbody>')

            ## artifact list
            for source_well, art, out_art in table_info:
                vol = out_art.udf.get('Adjusted Per Sample Volume (ul)', '')
                html.append('<tr><td style="width: 7%;">')
                if len(art.samples) < 1:
                    html.append('Pool: ' + art.name)
                else:
                    html.append('Sample: ' + art.samples[0].id)
                html.append('</td><td class="" style="width: 7%;">')
                html.append(source_well)
                html.append('</td><td class="" style="width: 7%;">')
                html.append(str(round(vol, 2)))
                html.append('</td></tr>')
            html.append('</tbody></table><br><br>')

            ## VISUAL Platemap
            ## column headers
            coulmns = range(1, 13)
            rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
            html.append('<table class="print-container-view"><thead><tr><th>&nbsp;</th>')
            for col in coulmns:
                html.append('<th>' + str(col) + '</th>')
            html.append('</tr></thead><tbody>')
            for rowname in rows:
                html.append('<tr style="height: 12%;"><td class="bold-column row-name">' + str(rowname) + '</td>')
                for col in coulmns:
                    well_location = str(rowname) + ":" + str(col)
                    if well_location in visual_map:
                        in_art, out_art = visual_map[well_location]
                        vol = out_art.udf.get('Adjusted Per Sample Volume (ul)', '')
                        # This only happens if there is an artifact in the well
                        # This assumes that all artifacts have the required UDFs
                        html.append('<td class="well" style="background-color: #CCC;">')
                        html.append('Project : ' + in_art.samples[0].project.name + '<br>')
                        if len(in_art.samples) > 1:
                            html.append('Pool Name : ' + out_art.name + '<br>')
                            html.append('Pool ID : ' + out_art.id + '<br>')
                        else:
                            html.append('Sample ID : ' + out_art.samples[0].id + '<br>')
                        html.append('Adjusted Per Sample Volume : ' + str(round(vol, 2)) + '<br>')
                        html.append('Source Well : ' + well_location + '<br>')
                    else:
                        # For wells that are empty:
                        html.append('<td class="well" style="">&nbsp;</td>')
                    html.append('</td>')
            html.append('</body></table>')

        html.append('</html>')
        file = open(str(resultfile) + ".html", "w")
        file.write(''.join(html).encode('utf-8'))
        file.close()


def main(lims, args):
    process = Process(lims, id=args.pid)
    SPM = SamplePlacementMap(process)
    SPM.make_html(args.res)


if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid',
                        help='Lims id for current Process')
    parser.add_argument('--res', default=sys.stdout,
                        help=('Result file'))
    args = parser.parse_args()

    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()
    main(lims, args)
