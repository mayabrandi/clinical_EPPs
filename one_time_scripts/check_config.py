

from genologics.lims import Lims
from genologics.config import BASEURI,USERNAME,PASSWORD
lims = Lims(BASEURI, USERNAME, PASSWORD)
import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO) 

from argparse import ArgumentParser


def get_process_types(lims, search_by):
    logging.info(f'getting process types')
    search_results = {}
    for automation in lims.get_automations():
        bash_string = automation.string
        if bash_string.find(search_by) == -1:
            continue
        for process_type in automation.process_types:
            if process_type.name[0:8]!='obsolete':
                if not process_type in search_results:
                    search_results[process_type.id] = [automation.name]
                else:
                    search_results[process_type.id].append(automation.name)
    logging.info('done')
    return search_results

def get_status(lims, search_results):
        
    logging.info("Searching for active workflows and steps.\n")
    workflows = lims.get_workflows()
    for workflow in workflows:
        if workflow.status == 'ACTIVE':
            print('')
            logging.info(f"Serching active workflow: {workflow.name}")
            for stage in workflow.stages:
                if not stage.step:
                    continue
                if stage.step.type.id in search_results.keys():
                    for trigger in stage.step.epp_triggers:
                        if trigger['name'] in search_results[stage.step.type.id]:
                            logging.info(trigger)


def main(args):
    lims = Lims(BASEURI, USERNAME, PASSWORD)

    search_results = get_process_types(lims, args.automation_string)
    get_status(lims, search_results)


if __name__ == "__main__":
    Parser = ArgumentParser()
    Parser.add_argument('-s', dest='automation_string',
                        help = 'Search automation by automation_string. Any subset of the automation bash string is valid. Could be a script name, eg: bcl2fastq.py, or a script argument, eg: CG002 - Aggregate QC (Library Validation) ')

    args = Parser.parse_args()
    main(args)