#!/usr/bin/env python3

import argparse
from collections import OrderedDict
import xml.etree.ElementTree as ET
import gate

parser = argparse.ArgumentParser(
    description='pairs IDs with text spans of a specified annotation'
    'type from an existing GATE annotation file and puts them in a schema as'
    'selection options',
)
parser.add_argument(
    '-s',
    '--schema-file',
    dest='schema_file',
    required='true',
    help='a sample schema file; used as template for the output schema'
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
    '--input-annotation',
    dest='input_annotation_type',
    required='true',
    help='the type of annotation from which IDs and text spans will be gathered'
    'from the source file'
)
parser.add_argument(
    '--output-annotation-path',
    dest='output_annotation_path',
    action='append',
    required='true',
    help='the type of annotation for which IDs and text spans will be supplied '
    'in the destination file.'
    'Must include an annotation type and a subfeature for which selections '
    'intend to be generated in the form of a path, e.g. annotation/feature.'
)
# parse CL arguments
args = parser.parse_args()
annotation_file = gate.Annotation(args.annotation_file)
schema_file = gate.Schema(args.schema_file)
write_file = args.write_file
input_annotation_type = args.input_annotation_type
output_annotation_paths = args.output_annotation_path

# find injection points in schema
# "restrictions" are what the specified annotation feature string will be
# restricted to
restriction_paths = []
for output_annotation_path in output_annotation_paths:
    element = output_annotation_path.split('/')[0]
    attribute = output_annotation_path.split('/')[1]

    restriction_paths.append(
        schema_file.root.find(
            ".//schema:element[@name='{element}']"
            "//schema:attribute[@name='{attribute}']"
            "//schema:restriction[@base='string']".format(
                element=element,
                attribute=attribute
            ),
            namespaces=schema_file.namespace
        ),
    )

# gather annotated text
text_with_nodes = OrderedDict()
for node in annotation_file.root.findall("./TextWithNodes/Node"):
    text_with_nodes.update({node.get('id'): node})

# compile list of restriction_strings from annotation file
restriction_strings = []
for annotation in annotation_file.get_annotations(
    annotation_type=input_annotation_type
):
        annotation_id = annotation.get('Id')
        start_node = int(
            list(text_with_nodes.keys()).index(annotation.get('StartNode'))
        )
        end_node = int(
            list(text_with_nodes.keys()).index(annotation.get('EndNode'))
        )
        string = ''.join(
            [x[1].tail for x in list(
                text_with_nodes.items()
            )[start_node:end_node]]
        )
        # trim string to include only first 3 and last 3 words
        if len(string.split()) > 6:
            string = ' (...) '.join(
                [
                    ' '.join(string.split()[:3]),
                    ' '.join(string.split()[-3:])
                ]
            )
        # formatting of feature string selection
        restriction_strings.append(
            '{ID} {string}'.format(
                ID=annotation.get('Id'),
                string=string
            )
        )

# populate schema with restriction_strings
for restriction_path in restriction_paths:
    restriction_path.clear()
    restriction_path.set('base', 'string')
    for restriction_string in restriction_strings:
        ET.SubElement(
            restriction_path,
            'enumeration',
            {'value':restriction_string}
        )

# write schema to file
ET.register_namespace('', schema_file.namespace['schema'])
schema_file.tree.write(
    write_file,
    encoding='UTF-8',
    xml_declaration=True,
    default_namespace=''
)
