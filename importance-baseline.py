#!/usr/bin/env python3

import os
import csv
import re
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
with open(baseline_file, 'r') as csvfile:
    baseline_dict = {}
    for row in csv.DictReader(csvfile):
        baseline_dict.update(
            {
                row['relation']:
                Baseline(
                    relation=row['relation'],
                    imp1=row['imp1'],
                    imp1_cert=row['imp1_cert'],
                    imp2=row['imp2'],
                    imp2_cert=row['imp2_cert'],
                    qual=row['qual'],
                    qual_cert=row['qual_cert']
                    )
                }
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
ImportanceAnnotation = namedtuple(
        'ImportanceAnnotation',
        ['abbrev', 'longform', 'scores']
        )

def schema_parse(abbrev=None, longform=None, scores=None):
    enumeration_dict = {}
    for enumeration in scores:
        digit = re.search('^\d+', enumeration).group()
        enumeration_dict.update({digit:enumeration})
    return ImportanceAnnotation(
        abbrev=abbrev,
        longform=longform,
        scores=enumeration_dict
        )

for k,v in schema_dict.items():
    if 'person 1' in k.lower():
        if 'importan' in k.lower():
            if 'certain' in k.lower():
                imp1_cert = schema_parse(
                    abbrev='imp1_cert',
                    longform=k,
                    scores=v
                    )
                continue
            else:
                imp1 = schema_parse(
                    abbrev='imp1',
                    longform=k,
                    scores=v
                    )
                continue
    if 'person 2' in k.lower():
        if 'importan' in k.lower():
            if 'certain' in k.lower():
                imp2_cert = schema_parse(
                    abbrev='imp2_cert',
                    longform=k,
                    scores=v
                    )
                continue
            else:
                imp2 = schema_parse(
                    abbrev='imp2',
                    longform=k,
                    scores=v
                    )
                continue
    if 'quality' in k.lower():
        if 'certain' in k.lower():
            qual_cert = schema_parse(
                abbrev='qual_cert',
                longform=k,
                scores=v
                )
            continue
        else:
            qual = schema_parse(
                abbrev='qual',
                longform=k,
                scores=v
                )
            continue

imp_annotation_scheme = [
    imp1,
    imp1_cert,
    imp2,
    imp2_cert,
    qual,
    qual_cert
    ]

# find consensus set
for x in input_file.get_annotation_set_names():
    if isinstance(x, str):
        if 'consensus' in x.lower():
            # makes sure relevant annotations are in this set
            if input_file.get_annotations(
                annotation_type='Relationship',
                annotation_set='consensus',
                ):
                consensus_set_name = x
consensus_set = input_file.get_annotations(
    annotation_type='Relationship',
    annotation_set=consensus_set_name,
    )

# edit consensus set
importance_prompts = [x.longform for x in imp_annotation_scheme]
unrecognized_relations = {}
for annotation in consensus_set:
    # remove preexisting importance annotations
    for feature in annotation:
        for element in feature:
            if element.tag == 'Name':
                if (('type' in element.text.lower()) and
                    ('relation' in element.text.lower())):
                    relation = feature.find('.//Value').text
                    break
                if element.text in importance_prompts:
                    annotation.remove(feature)
                    break
    # tally unrecognized relation types
    if relation not in baseline_dict:
        if relation in unrecognized_relations:
            unrecognized_relations[relation] += 1
        else:
            unrecognized_relations.update({relation: 1})
        continue
    # create baseline importance annotations
    baseline = baseline_dict[relation]._asdict()
    for dimension in imp_annotation_scheme:
        feature = ET.SubElement(annotation, 'Feature')
        name = ET.SubElement(
            feature,
            'Name',
            className='java.lang.String'
            )
        value = ET.SubElement(
            feature,
            'Value',
            className='java.lang.String'
            )
        name.text = dimension.longform
        score = baseline[dimension.abbrev]
        value.text = dimension.scores[score] 

# writes edits to output file
input_file.tree.write(
    output_file,
    encoding='UTF-8',
    xml_declaration=True
    )
