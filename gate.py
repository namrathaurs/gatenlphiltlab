#!/usr/bin/env python3

from collections import namedtuple
import re
import xml.etree.ElementTree as ET
import skll
from collections import Counter

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

    def get_annotations(self, *, annotation_type=None, annotation_set=None):
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

    def get_attributes(self, annotation_type):
        attributes = self.root.findall(".//schema:element[@name='{}']//schema:attribute".format(annotation_type), namespaces=self.namespace)
        return attributes


def pair_annotations(annotations1, annotations2, *, annotation_type=None, schema=None):
    annotations1_list, annotations2_list = list(annotations1), list(annotations2)

    # Build list of annotation pairs
    annotation_pairs = []
    for annotation1 in annotations1_list:
        for annotation2 in annotations2_list:
            # if annotation spans overlap
            if ( ( int(annotation1.get('StartNode')) >= int(annotation2.get('StartNode'))
                    and int(annotation1.get('StartNode')) < int(annotation2.get('EndNode')) )
                    or ( int(annotation1.get('EndNode')) > int(annotation2.get('StartNode'))
                        and int(annotation1.get('EndNode')) <= int(annotation2.get('EndNode')) ) ):
                annotation_pairs.append((annotation1, annotation2))
                annotations2_list.remove(annotation2)
                break
    annotations1_list.clear() and annotations2_list.clear()

    # Unpack Names and Values of each annotation
    content_pairs = []
    for pair in annotation_pairs:
        new_pair = []
        for annotation in pair:
            annotation = { feature.findtext('./Name') : feature.findtext('./Value') for feature in list(annotation) }
            new_pair.append(annotation)
        content_pairs.append(new_pair)

    content_pairs = tuple(content_pairs)

    # Compile comparison sets for each annotation attribute
    ComparisonSet = namedtuple('ComparisonSet', ['attribute', 'annotator1', 'annotator2'])
    attributes = [ attribute.get('name') for attribute in schema.get_attributes(annotation_type) ]
    comparison_sets = []
    for attribute in attributes:
        annotator1 = tuple( annotation[0].get(attribute) for annotation in content_pairs )
        annotator2 = tuple( annotation[1].get(attribute) for annotation in content_pairs )
        attribute_annotations = ComparisonSet(attribute, annotator1, annotator2)
        comparison_sets.append(attribute_annotations)

    return comparison_sets

def kappa(comparison_set, weights=None):
    new_comparison_set = comparison_set
    new_comparison_set = new_comparison_set._replace(annotator1=tuple( re.sub(r'(\d+).*', r'\1', annotation) for annotation in comparison_set.annotator1 if annotation ))
    new_comparison_set = new_comparison_set._replace(annotator2=tuple( re.sub(r'(\d+).*', r'\1', annotation) for annotation in comparison_set.annotator2 if annotation ))
    if (len(new_comparison_set.annotator1) == len(new_comparison_set.annotator2)
        and not (len(new_comparison_set.annotator1) <= 0 or len(new_comparison_set.annotator2) <= 0) ):
        #print(new_comparison_set.attribute)
        #print(Counter(list(zip(new_comparison_set.annotator1, new_comparison_set.annotator2))))
        return skll.kappa(new_comparison_set.annotator1, new_comparison_set.annotator2, weights=weights)
