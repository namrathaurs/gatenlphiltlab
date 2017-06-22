#!/usr/bin/env python3

import argparse
from collections import OrderedDict
import xml.etree.ElementTree as ET
import gate

parser = argparse.ArgumentParser(
    description='takes person mentions from an existing GATE annotation'
    ' file and puts them in a schema as selection options',
    )
parser.add_argument(
    '-i',
    '--annotation-file',
    dest='annotation_file',
    required='true',
    help='the input; a GATE annotation file with Person Mentions'
    )
parser.add_argument(
    '-o',
    '--write-file',
    dest='write_file',
    required='true',
    help='the write file; the resultant GATE schema'
    )
parser.add_argument(
    '-s',
    '--schema-file',
    dest='schema_file',
    required='true',
    help='a sample schema file; used as template for the output schema'
    )
# parse CL arguments
args = parser.parse_args()
annotation_file = gate.Annotation(args.annotation_file)
schema_file = gate.Schema(args.schema_file)
write_file = args.write_file

# find injection point in schema
restrictions = [
    # pers1
    schema_file.root.find(
        ".//schema:element[@name='Relationship']"
        "//schema:attribute[@name='1. Person 1']"
        "//schema:restriction[@base='string']",
        namespaces=schema_file.namespace
        ),
    # pers2
    schema_file.root.find(
        ".//schema:element[@name='Relationship']"
        "//schema:attribute[@name='3. Person 2']"
        "//schema:restriction[@base='string']",
        namespaces=schema_file.namespace
        )
    ]

# compile list of persons from annotation file
text_with_nodes = OrderedDict()
for node in annotation_file.root.findall("./TextWithNodes/Node"):
    text_with_nodes.update({node.get('id'): node})

persons = []
for annotation in annotation_file.get_annotations(annotation_type='Person'):
    annotation_id = annotation.get('Id')
    start_node = int(
        list(text_with_nodes.keys()).index(annotation.get('StartNode'))
        )
    end_node = int(
        list(text_with_nodes.keys()).index(annotation.get('EndNode'))
        )
    string = ''.join(
        [x[1].tail for x in list(text_with_nodes.items())[start_node:end_node]]
        )
    persons.append('{}\t{}'.format(annotation.get('Id'), string))

# populate schema with person mentions
for restriction in restrictions:
    restriction.clear()
    restriction.set('base', 'string')
    for person in persons:
        ET.SubElement(
            restriction,
            'enumeration',
            {'value':person}
            )

# write schema to file
ET.register_namespace('', schema_file.namespace['schema'])
schema_file.tree.write(
    write_file,
    encoding='UTF-8',
    xml_declaration=True,
    default_namespace=''
    )
