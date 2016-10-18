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


    def get_annotation_sets(self):
        annotation_sets = []
        for annotation_set in self.root.iter('AnnotationSet'):
            annotation_sets.append(annotation_set.get('Name'))
        return annotation_sets

    # TODO: root.setter if annotation set specified

    def get_annotations(self, annotation_type, *, annotation_set):
        text = open(self.filename).read()
        if annotation_set:
            try:
                text = re.search(r'<AnnotationSet Name="{}">.*?</AnnotationSet>'.format(annotation_set), text, re.DOTALL).group()
            except AttributeError:
                raise InputError("'{}' is not a valid annotation set".format(annotation_set))
        return re.findall(r'<Annotation\s+?.*?Type="{}".*?>.*?</Annotation>'.format(annotation_type), text, re.DOTALL)
