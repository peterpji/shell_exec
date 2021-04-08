"""
Install locally with:
cd api-markettailor
pip install -e .
"""
import os

import setuptools

DIR = os.path.abspath(os.path.dirname(__file__))

setuptools.setup(
    name='exec',
    version='1.0.0',
    description='Adds exec.py tool to the command line.',
    packages=setuptools.find_packages(include=['exec', 'exec.*']),
    setup_requires=[
        'bandit',
        'black',
        'coverage',
        'flake8',
        'isort',
        'pre-commit',
        'pylint',
        'safety',
    ],
    entry_points={'console_scripts': ['exec=exec.exec:main']},  # TODO Might need to be put in a package?
)
