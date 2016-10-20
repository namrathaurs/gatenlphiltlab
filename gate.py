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

def pair_annotations(annotations1, annotations2):
    annotations1_list, annotations2_list = list(annotations1), list(annotations2)
    annotations_dict = {}
    for annotation1 in annotations1_list:
        for annotation2 in annotations2_list:
            if ((int(annotation1.get('StartNode')) >= int(annotation2.get('StartNode'))
                    and int(annotation1.get('StartNode')) < int(annotation2.get('EndNode')))
                    or (int(annotation1.get('EndNode')) > int(annotation2.get('StartNode'))
                        and int(annotation1.get('EndNode')) <= int(annotation2.get('EndNode')))):
                annotations_dict.update({annotation1:annotation2})
                annotations2_list.remove(annotation2)
                break
    annotations1_list.clear()
    annotations2_list.clear()
    for x in list(iter(annotations_dict)):
        print(('a', x.get('StartNode'), x.get('EndNode')), ('b', annotations_dict[x].get('StartNode'), annotations_dict[x].get('EndNode')))
    return annotations_dict
