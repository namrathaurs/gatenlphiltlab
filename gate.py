#!/usr/bin/env python3

from functools import reduce
import itertools
from lxml import etree

class AnnotationFile:
    """Given a GATE XML annotation file, returns an AnnotationFile object.
    """
    def __init__(self, filename):
        self._filename = filename
        self._tree = etree.parse(self.filename)
        self._root = self.tree.getroot()
        self._nodes = None
        self._text_with_nodes = None
        self._annotations = None

    @property
    def filename(self):
        return self._filename

    @property
    def tree(self):
        return self._tree

    @property
    def root(self):
        return self._root

    @property
    def text(self):
        return "".join( self.text_with_nodes.itertext() )

    @property
    def nodes(self):
        if not self._nodes:
            nodes = self.text_with_nodes.getchildren()
            self._nodes =  {
                int(node.get("id")) : node for node in nodes
            }
            return self._nodes
        else:
            return self._nodes

    @property
    def text_with_nodes(self):
        if not self._text_with_nodes:
            self._text_with_nodes = self.root.find(".//TextWithNodes")
            return self._text_with_nodes
        else:
            return self._text_with_nodes

    @property
    def annotation_set_names(self):
        if not self._annotation_set_names:
            self._annotation_set_names = [
                annotation_set.get("Name")
                for annotation_set
                in self.root.findall(".//AnnotationSet")
            ]
            return self._annotation_set_names
        else:
            return self._annotation_set_names

    @property
    def annotations(self):
        if not self._annotations:
            self._annotations = [ x for x in self.iter_annotations() ]
            return self._annotations
        else:
            return self._annotations

    def iter_annotations(self):
        annotations = self.root.findall(
            ".//Annotation"
        )
        for x in annotations:
            yield Annotation(x)

class Annotation:
    def __init__(self, annotation):
        self._annotation = annotation
        self._type = annotation.get("Type")
        self._id = annotation.get("Id")
        self._start_node = int(annotation.get("StartNode"))
        self._end_node = int(annotation.get("EndNode"))
        self._continuations = []

        annotation_set_name = annotation.getparent().get("Name")
        if annotation_set_name:
            self._annotation_set_name = annotation_set_name
        else:
            self._annotation_set_name = ""

        if self._type == "Attribution":
            self._caused_event_id = None
            for feature in self.features:
                if feature.name.lower() == "caused_event":
                    self._caused_event_id = feature.value.split()[0]
                    break

    @property
    def type(self):
        return self._type

    @property
    def id(self):
        return self._id

    @property
    def start_node(self):
        return self._start_node

    @property
    def end_node(self):
        return self._end_node

    @property
    def features(self):
        return [ Feature(x) for x in self._annotation if x.tag == "Feature" ]

    @property
    def annotation_set_name(self):
        return self._annotation_set_name

    @property
    def continuations(self):
        return self._continuations

    def iter_spans(self):
        return itertools.chain( [self], ( x for x in self.continuations ) )

    def get_text(self, annotation_file):
        return "".join(
            annotation_file.nodes[node].tail
            for node in sorted(
                self.get_concatenated_char_set().intersection(
                    annotation_file.nodes.keys()
                )
            )
        )

    def get_concatenated_text(self, text_with_nodes, separator):
        return separator.join(
            x.get_text(text_with_nodes) for x in self.iter_spans()
        )

    def get_char_set(self):
        return frozenset(
            range(
                self.start_node,
                self.end_node
            )
        )

    def get_concatenated_char_set(self):
        if self.continuations:
            return reduce(
                lambda x,y : frozenset( x | y.get_char_set() ),
                self.iter_spans(),
                next(self.iter_spans()).get_char_set()
            )
        else: return self.get_char_set()

    def add_continuation(self, annotation):
        self._continuations.append(annotation)

    def get_caused_event(self, events):
        return next(
            ( x for x in events if x._id == self._caused_event_id ),
            None
        )

class Feature:
    def __init__(self, feature):
        self._feature = feature
        self._name = feature.find("./Name")
        self._value = feature.find("./Value")

    @property
    def name(self):
        return self._name.text

    @name.setter
    def name(self, name):
        self._name.text = name

    @property
    def value(self):
        return self._value.text

    @value.setter
    def value(self, value):
        self._value.text = value

class Schema:
    def __init__(self, filename):
        self.filename = filename
        self.tree = etree.parse(self.filename)
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

def find_from_index(index,
                    source_list,
                    match_function,
                    reverse=False,
                    greedy=True):
    if reverse:
        try:
            list_from_index = source_list[index-1::-1]
        except IndexError:
            raise StopIteration()
    else:
        try:
            list_from_index = source_list[index+1::1]
        except IndexError:
            raise StopIteration()
    if greedy:
        for x in list_from_index:
            if match_function(x):
                yield x
    else:
        for x in list_from_index:
            if match_function(x):
                yield x
            else:
                raise StopIteration()

def concatenate_annotations(annotation_iterable):
    """Given an iterable of Annotation objects, returns a list of Annotations
    objects such that each Annotation's continuations list is populated
    appropriately, less all continuation annotations
    """

    annotations = sorted(
        sorted(
            annotation_iterable,
            key=(lambda x: x.annotation_set_name)
        ),
        key=(lambda x: x.end_node)
    )

    for i, annotation in enumerate(annotations):
        if "_continuation" in annotation.type:
            continuation = annotation
            base_annotation_type = (
                continuation.type.replace("_continuation","")
            )
            continued_annotation = next(
                find_from_index(
                    i,
                    annotations,
                    lambda x : x.type == base_annotation_type,
                    reverse=True,
                )
            )
            continued_annotation.add_continuation(annotation)

    return [
        annotation
        for annotation in annotations
        if not annotation.type.endswith("_continuation")
    ]

def filter_annotations_by_type(annotation_iterable,
                               annotation_types,
                               with_continuations=False):
    """Given an iterable of Annotation objects, return a generator which yields
    all Annotations of the given type(s)"""
    base_types = [ x.lower() for x in annotation_types ]
    key_types = []
    for x in base_types:
        key_types.append(x)
        if with_continuations:
            key_types.append(x + "_continuation")

    return [
        annotation
        for annotation in annotation_iterable
        if annotation.type.lower() in key_types
    ]

def get_feature_by_name(name,
                        annotation):
    return next(
        (
            feature
            for feature in annotation.features
            if name.lower() in feature.name.lower()
        ),
        None
    )

def is_overlapping(annotations):
    if len(annotations) == 0:
        raise Exception("Can't compare to nothing!")
    return all(
        not (
            annotation
            .get_concatenated_char_set()
            .isdisjoint(
                annotations[i+1]
                .get_concatenated_char_set()
            )
        )
        for i, annotation in enumerate( annotations[:-1] )
    )
