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
    'schema_file',
    metavar='schema-file',
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
input_file = gate.Annotation(parser.parse_args().input_file)
output_file = parser.parse_args().output_file
schema_file = gate.Schema(parser.parse_args().schema_file)

# TODO: export baseline and its alteration to its own file.
# This prog doesn't need to process the CSV every time it's run.
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

for x in input_file.get_annotation_set_names():
    if isinstance(x, str):
        if 'consensus' in x.lower():
            if input_file.get_annotations(
                annotation_type='Relationship',
                annotation_set='consensus',
                ):
                consensus_set = x

input_file.get_annotations(
    annotation_type='Relationship',
    annotation_set=consensus_set,
    )



for x in schema_file.root.findall(
    ".//schema:element[@name='Relationship']"
    "//schema:attribute[@name]"
    "//schema:enumeration[@value]",
    namespaces=schema_file.namespace
    ):
    print(x.get('value'))
    continue
    if x.get('value') in baseline_dict:
        print('hit')
    else:
        print('miss')
