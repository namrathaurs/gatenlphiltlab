#!/usr/bin/env python3

import os
import csv
from collections import namedtuple
import argparse
import xml.etree.ElementTree as ET
import gate

# command-line argument parsing
parser = argparse.ArgumentParser(
    description='''automatically supplies baseline annotations to'''
    ''' Importance annotation files.'''
    )
parser.add_argument(
    'schema_file',
    metavar='schema-file',
    type=argparse.FileType(mode='r'),
    )
parser.add_argument(
    'input_file',
    metavar='input-file',
    type=argparse.FileType(mode='r'),
    )
parser.add_argument(
    'output_file',
    metavar='output-file',
    type=argparse.FileType(mode='w+b'),
    )

# instantiate input files as appropriate gate objects
schema_file = gate.Schema(parser.parse_args().schema_file)
input_file = gate.Annotation(parser.parse_args().input_file)

output_file = parser.parse_args().output_file


# TODO: export baseline and its alteration to its own file.
# This prog doesn't need to process the CSV every time it's run.

# parse baseline annotations from csv into dictionary
## keys = type of relation
## values = namedtuple of baseline annotations
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

# find consensus set
for x in input_file.get_annotation_set_names():
    if isinstance(x, str):
        if 'consensus' in x.lower():
            # makes sure rel annotations are in this set
            if input_file.get_annotations(
                annotation_type='Relationship',
                annotation_set='consensus',
                ):
                consensus_set_name = x
consensus_set = input_file.get_annotations(
    annotation_type='Relationship',
    annotation_set=consensus_set_name,
    )

# parse schema into dictionary
## keys = name of attribute
## values = list of possible values for attribute
schema_dict = {}
for x in schema_file.root.findall(
    ".//schema:element[@name='Relationship']"
    "//schema:attribute",
    namespaces=schema_file.namespace
    ):
    name = x.get('name')
    enumerations = []
    for enumeration in x.findall(
            ".//schema:enumeration",
            namespaces=schema_file.namespace
            ):
        enumerations.append(enumeration.get('value'))

    schema_dict.update({name:enumerations})

# map schema names to baseline names
baseline_ids = [
    'imp1',
    'imp1_cert',
    'imp2',
    'imp2_cert',
    'qual',
    'qual_cert',
    ]
baseline_schema_map = {x:'' for x in baseline_ids}
Person1 = []
Person2 = []
Qual = []
for x in schema_dict.keys():
    if 'person 1' in x.lower():
        Person1.append(x)
    if 'person 2' in x.lower():
        Person2.append(x)
    if 'quality' in x.lower():
        Qual.append(x)
for x in Person1:
    if 'importan' in x.lower():
        if 'certain' in x.lower():
            baseline_schema_map.update({'imp1_cert':x})
            continue
        else:
            baseline_schema_map.update({'imp1':x})
for x in Person2:
    if 'importan' in x.lower():
        if 'certain' in x.lower():
            baseline_schema_map.update({'imp2_cert':x})
            continue
        else:
            baseline_schema_map.update({'imp2':x})
for x in Qual:
    if 'certain' in x.lower():
        baseline_schema_map.update({'qual_cert':x})
        continue
    else:
        baseline_schema_map.update({'qual':x})


quit()

# edits consensus set
for annotation in consensus_set:
    for feature in annotation:
        for element in feature:
            if element.tag == 'Name':
                element.text = 'fqwhgads'

# writes edits to output file
input_file.tree.write(
    output_file,
    encoding='UTF-8',
    xml_declaration=True
    )
