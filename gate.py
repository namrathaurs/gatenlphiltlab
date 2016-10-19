#!/usr/bin/env python3

from collections import namedtuple
import re
import xml.etree.ElementTree as ET

class InputError(Exception):
    pass

class GateAnnotation:
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

def kappa(annotations1, annotations2, *, schema=None):
    annotations1_list, annotations2_list = list(annotations1), list(annotations2)
    return next(annotations1)
    #annotation_pairs = {annotations1
