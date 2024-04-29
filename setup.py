"""
Install locally with:
pip install -e .
"""

import os
import setuptools

DIR = os.path.abspath(os.path.dirname(__file__))

setuptools.setup(
    name='run',
    version='1.0.0',
    description='Adds run.py tool to the command line.',
    packages=setuptools.find_packages(where='src', include=['*']),
    extras_require={},
    entry_points={'console_scripts': ['run=src.main:main']},
)
