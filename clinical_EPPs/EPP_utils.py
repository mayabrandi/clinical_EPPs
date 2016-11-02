#!/usr/bin/env python

def parse_application_tag(app_tag):
    """Parse out the components of the application tag."""
    if len(app_tag) == 10:
        data = {'analysis': app_tag[:3], 'library': app_tag[3:6]}
        if app_tag[6] == 'K':
            data['reads'] = int(app_tag[7:]) * 1000
        elif app_tag[6] == 'R':
            data['reads'] = int(app_tag[7:]) * 1000000
        elif app_tag[6] == 'C':
            genome_bases = 3100000000
            bases_per_read = 150
            cov = int(app_tag[7:])
            data['coverage'] = cov
            data['reads'] = int(float(cov*genome_bases)/bases_per_read)

    elif len(app_tag) == 9:
        data = {'analysis': app_tag[:3], 'library': app_tag[3:6],
                'reads': int(app_tag[6:]) * 1000000}

    elif len(app_tag) == 8:
        # EXOSX100, EXSTA100
        data = {'analysis': 'EXO', 'library': 'SXT',
                'reads': int(app_tag[5:]) * 1000000}

    elif len(app_tag) == 12:
        # EXSTATRIO100
        data = {'analysis': 'EXO', 'library': 'SXT', 'reads': 100000000}

    else:
        raise ValueError("unknown application tag: {}".format(app_tag))

    return data
