#!/usr/bin/env python3

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
            return self.root.iterfind(".//AnnotationSet/Annotation[@Type='{}']".format(annotation_type))
        return self.root.iterfind(".//Annotation[@Type='{}']".format(annotation_type))

def annotation_kappa(annotations1, annotations2, *, schema=None):
    annotations1_dict = {annotation.get('Type'): annotation for annotation in annotations1}
    annotations2_dict = {annotation.get('Type'): annotation for annotation in annotations2}
    annotations = {}
    for annotation1 in annotations1_dict.keys():
        for annotation2 in annotations2_dict.keys():
            if annotations1 == annotations2:
                annotations.update(annotations1_dict.pop(annotation1), annotations2_dict.pop(annotation2))
    return annotations
