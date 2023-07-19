#!/usr/bin/env python

from distutils.core import setup
import glob

setup(name='clinical_EPPs',
        version='1.0',
        description='',
        author='Maya Brandi',
        author_email='maya.brandi@scilifelab.se',
        packages=['clinical_EPPs'],
        scripts=glob.glob("EPPs/*.py")
     )
