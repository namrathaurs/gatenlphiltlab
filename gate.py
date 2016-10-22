#!/usr/bin/env python3

from collections import namedtuple
import re
import xml.etree.ElementTree as ET

class InputError(Exception):
    pass

class Annotation:
    def __init__(self, filename):
        self.filename = filename

    def filename(self, filename):
        self.filename = filename

    @property
    def tree(self):
        return ET.parse(self.filename)

    @property
    def root(self):
        return self.tree.getroot()

    def get_annotation_set_names(self):
        return [annotation_set.get('Name') for annotation_set in self.root.iter("AnnotationSet")]

    def get_annotations(self, annotation_type, *, annotation_set=None):
        if annotation_set:
            return self.root.iterfind(".//AnnotationSet[@Name='{}']/Annotation[@Type='{}']".format(annotation_set, annotation_type))
        else:
            return self.root.iterfind(".//Annotation[@Type='{}']".format(annotation_type))

class Schema:
    def __init__(self, filename):
        self.filename = filename
        self.namespace = {'schema':'http://www.w3.org/2000/10/XMLSchema'}

    def filename(self, filename):
        self.filename = filename

    @property
    def tree(self):
        return ET.parse(self.filename)

    @property
    def root(self):
        return self.tree.getroot()

    def get_annotations(self, annotation_type):
        attributes = self.root.findall(".//schema:element[@name='{}']//schema:attribute".format(annotation_type), namespaces=self.namespace)
        return attributes





def pair_annotations(annotations1, annotations2):
    annotations1_list, annotations2_list = list(annotations1), list(annotations2)

    annotation_pairs = []
    for annotation1 in annotations1_list:
        for annotation2 in annotations2_list:
            if ( ( int(annotation1.get('StartNode')) >= int(annotation2.get('StartNode'))
                    and int(annotation1.get('StartNode')) < int(annotation2.get('EndNode')) )
                    or ( int(annotation1.get('EndNode')) > int(annotation2.get('StartNode'))
                        and int(annotation1.get('EndNode')) <= int(annotation2.get('EndNode')) ) ):
                annotation_pairs.append((annotation1, annotation2))
                annotations2_list.remove(annotation2)
                break
    annotations1_list.clear() and annotations2_list.clear()

    content_pairs = []
    for pair in annotation_pairs:
        new_pair = []
        for annotation in pair:
            annotation = { feature.findtext('./Name') : feature.findtext('./Value') for feature in list(annotation) }
            new_pair.append(annotation)
        content_pairs.append(new_pair)

    return content_pairs

#def kappa(content_pairs, schema_file/contents):
