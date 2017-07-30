#!/usr/bin/env python3

from collections import namedtuple
import re
from lxml import etree as ET
import skll
from collections import Counter
from pprint import pprint

class InputError(Exception):
    pass


class AnnotationFile:
    #TODO: make get_text_with_nodes() function
    def __init__(self, filename):
        self.filename = filename
        self.tree = ET.parse(self.filename)
        self.root = self.tree.getroot()
        self.annotation_set_names = [
            annotation_set.get("Name")
            for annotation_set
            in self.root.findall(".//AnnotationSet")
        ]

    def get_annotations(self,
                        *,
                        annotation_type=None,
                        annotation_set=None):
        if annotation_set:
            annotations = self.root.findall(
                ''.join(
                    [
                        ".//AnnotationSet[@Name='{}']".format(annotation_set),
                        "/Annotation[@Type='{}']".format(annotation_type)
                    ]
                )
            )
        elif annotation_type:
            annotations = self.root.findall(
                ".//Annotation[@Type='{}']".format(annotation_type)
            )
        else:
            annotations = self.root.findall(
                ".//Annotation"
            )

        return ( Annotation(x) for x in annotations )

class Annotation:
    def __init__(self, annotation):
        self._annotation_type = annotation.get("Type")
        self._annotation_set = annotation.getparent().get("Name")
        self._start_node = annotation.get("StartNode")
        self._end_node = annotation.get("EndNode")
        self._features = [ Feature(x) for x in annotation if x.tag == "Feature" ]
        self._caused_event_id = None

        if self._annotation_type == "Attribution":
            for feature in self._features:
                if feature._name == "Caused_Event":
                    self._caused_event_id = feature._value.split(' ')[0]
                    break


class Feature:
    def __init__(self, feature):
        self._name = feature.find("./Name").text
        self._value = feature.find("./Value").text

"""
class AnnotationGroup:
    def __init__(self, annotation_iteratable):

    def group_annotations(annotation_iterable):
"""

class Schema:
    def __init__(self, filename):
        self.filename = filename
        self.tree = ET.parse(self.filename)
        self.root = self.tree.getroot()
        self.namespace = {
            'schema':'http://www.w3.org/2000/10/XMLSchema'
        }

    def get_attributes(self, annotation_type):
        attributes = self.root.findall(
            ".//schema:element[@name='{}']"
            "//schema:attribute".format(annotation_type),
            namespaces=self.namespace
        )
        return attributes


def pair_annotations(annotations1,
                     annotations2,
                     *,
                     annotation_type=None,
                     schema=None):

    annotations1_list = list(annotations1)
    annotations2_list = list(annotations2)

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
        annotator1 = tuple( annotation_pair[0].get(attribute) for annotation_pair in content_pairs )
        annotator2 = tuple( annotation_pair[1].get(attribute) for annotation_pair in content_pairs )
        attribute_annotations = ComparisonSet(attribute, annotator1, annotator2)
        comparison_sets.append(attribute_annotations)

    # set of annotations that fit the given attribute (attribute_annotations)
    return comparison_sets

def kappa(comparison_set, weights=None):

    if len(comparison_set.annotator1) == len(comparison_set.annotator2):

        new_comparison_set = comparison_set

        if weights == None:
        # skll.kappa accepts only int-like arguments,
        # so, given a set of string annotations, each will
        # be assigned a unique int id.
        # this is only statistically accurate when calculating an unweighted kappa
        # since only then do the distances between annotations not matter.

            # store a set of annotations...
            annotation_dict = {}
            for annotations in [
                comparison_set.annotator1,
                comparison_set.annotator2
            ]:
                for annotation in annotations:
                    annotation_dict.update({annotation : None})

            # then assign ints as ids
            id = 1
            for k in annotation_dict:
                annotation_dict.update({k : str(id)})
                id += 1

            def annotation_int(annotations):
                for annotation in annotations:
                    if annotation in annotation_dict:
                        yield re.sub(
                            annotation,
                            annotation_dict.get(annotation),
                            annotation
                        )

            # replace the annotation strings with int labels
            new_comparison_set = new_comparison_set._replace(
                annotator1=tuple(
                    annotation_int(comparison_set.annotator1)
                ),
                annotator2=tuple(
                    annotation_int(comparison_set.annotator2)
                )
            )

            annotator1 = new_comparison_set.annotator1
            annotator2 = new_comparison_set.annotator2

        else:

            def annotation_int(annotations):
                for annotation in annotations:
                    if annotation:
                        yield re.sub(
                            r'(\d+).*',
                            r'\1',
                            annotation
                        )
                        next()
                    else:
                        yield annotation
                        next()

            new_comparison_set = new_comparison_set._replace(
                annotator1=tuple(
                    annotation_int(comparison_set.annotator1)
                ),
                annotator2=tuple(
                    annotation_int(comparison_set.annotator2)
                )
            )

            annotator1 = new_comparison_set.annotator1
            annotator2 = new_comparison_set.annotator2


        kappa_score = skll.kappa(
            annotator1,
            annotator2,
            weights=weights
        )

        kappa_length = len(new_comparison_set.annotator1)

    return dict(
        {
        'score' : kappa_score,
        'length' : kappa_length
        }
    )

