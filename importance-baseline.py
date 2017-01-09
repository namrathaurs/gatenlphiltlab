#!/usr/bin/env python3

import os
import csv
from collections import namedtuple
import argparse
import xml.etree.ElementTree as ET
import gate

parser = argparse.ArgumentParser(
    description='''automatically supplies baseline annotations to'''
    ''' Importance annotation files.'''
    )
parser.add_argument(
    'schema',
    type=argparse.FileType(mode='r', encoding='UTF-8'),
    )
parser.add_argument(
    'input_file',
    metavar='input-file',
    type=argparse.FileType(mode='r', encoding='UTF-8'),
    )
parser.add_argument(
    'output_file',
    metavar='output-file',
    type=argparse.FileType(mode='w', encoding='UTF-8'),
    )
input_file = parser.parse_args().input_file
output_file = parser.parse_args().output_file
schema = gate.Schema(parser.parse_args().schema)
baseline_file = os.path.join(
    os.path.dirname(
        os.path.realpath(__file__)
        ),
    'baseline.csv'
    )
Baseline = namedtuple(
    'Baseline',
    [
        'relation',
        'imp1',
        'imp1_cert',
        'imp2',
        'imp2_cert',
        'qual',
        'qual_cert'
        ]
    )
baseline = []
with open(baseline_file, 'r') as csvfile:
    for row in csv.DictReader(csvfile):
        baseline.append(
            Baseline(
                relation=row['relation'],
                imp1=row['imp1'],
                imp1_cert=row['imp1_cert'],
                imp2=row['imp2_cert'],
                imp2_cert=row['imp2_cert'],
                qual=row['qual'],
                qual_cert=row['qual_cert']
                )
            )
baseline_dict = {}
for x in baseline:
    baseline_dict.update({x.relation: x})
baseline.clear()
for x in schema.root.findall(
    ".//schema:element[@name='Relationship']"
    "//schema:attribute[@name='3.Type of Relationship']"
    "//schema:enumeration[@value]",
    namespaces=schema.namespace
    ):
    if x.get('value') in baseline_dict:
        print('hit')
    else:
        print('miss')
