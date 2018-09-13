#!/usr/bin/env python
from argparse import ArgumentParser

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD

from genologics.entities import Process, Artifact

import logging
import sys


DESC = """Script to aggregate fields and qc flaggs from previous qc-steps

Written by Maya Brandi, Clinical Genomics, Stockholm, Sweden"""


class CopyUDF():
    def __init__(self, process):
        self.process = process
        self.copy_tasks = {}
        self.source_step_types = {}
        self.failded_udfs = []
        self.in_arts = [a for a in process.all_inputs() if a.type=='Analyte']
   
    def get_udfs(self):
        for udf, value in self.process.udf.items():
            if 'Copy task' in udf:
                k,v = udf.split('-')
                if v.strip() == 'Source Step':
                    self.source_step_types[value] = []
                if k.strip() in self.copy_tasks.keys():
                    self.copy_tasks[k.strip()][v.strip()] = value
                else:
                    self.copy_tasks[k.strip()] = {v.strip():value}
        for copy_task , source in self.copy_tasks.items():
            self.source_step_types[source['Source Step']].append(source['Source Field'])


    def copy_udfs(self):
        for art in self.in_arts:
            qc_flag = ''
            source_steps = self._get_correct_processes(art)
            for type, source_step in source_steps.items():
                for output in source_step.outputs_per_input(art.id):
                    qc_flag_update = Artifact(lims, id=output.id).qc_flag
                    if not qc_flag_update == 'UNKNOWN':
                        if not qc_flag == 'FAILED':
                            qc_flag = qc_flag_update
                        for udf in self.source_step_types[source_step.type.name]:
                            try:
                                art.udf[udf] = float(output.udf[udf])
                            except:
                                try:
                                    art.udf[udf] = str(output.udf[udf])
                                except:
                                    self.failded_udfs.append(art.name)
                                    pass
                
            art.qc_flag = qc_flag
            art.put()

    def _get_correct_processes(self, art):
        source_steps = {}
        processes = lims.get_processes(inputartifactlimsid=art.id)
        for process in processes:
            process_type = process.type.name
            if process_type in self.source_step_types.keys():
                if process_type not in source_steps.keys(): 
                    source_steps[process_type] = process
                elif source_steps[process_type].id < process.id:
                    source_steps[process_type] = process
        return source_steps


def main(lims, args):
    process = Process(lims, id = args.pid)
    CUDF = CopyUDF(process)
    CUDF.get_udfs()
    CUDF.copy_udfs()

    if CUDF.failded_udfs:
        failed = ' ,'.join(list(set(CUDF.failded_udfs)))
        sys.exit('failed to copy some udfs for sample(s): '+ failed)
    else:
        print >> sys.stderr, 'UDFs were succsessfully copied!'

if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('-p', dest = 'pid',
                        help='Lims id for current Process' )

    args = parser.parse_args()
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()

    main(lims, args)
