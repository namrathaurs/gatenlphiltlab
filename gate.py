#!/usr/bin/env python3

import re

class GateAnnotation:
    def __init__(self, filename):
        self.filename = filename

    def get_name(self):
        return self.filename

    def get_annotations(self, annotation_type, annotation_set):
        text = open(self.filename).read()
        if annotation_set:
            try:
                text = re.search(r'<AnnotationSet Name="{}">.*?</AnnotationSet>'.format(annotation_set), text, re.DOTALL).group()
            except AttributeError:
                print("'{}' is not a valid annotation set".format(annotation_set))
                quit()
        return re.findall(r'<Annotation\s+?.*?Type="{}".*?>.*?</Annotation>'.format(annotation_type), text, re.DOTALL)
    
    def get_annotation_sets(self):
        text = open(self.filename).read()
