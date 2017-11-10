#!/usr/bin/env python3

from functools import reduce
import itertools
from lxml import etree
import intervaltree


class AnnotationFile:
    def __init__(self, filename):
        self._filename = filename
        self._tree = etree.parse(self.filename)
        self._root = self.tree.getroot()
        self._nodes = None
        self._text_with_nodes = None
        self._annotations = None
        self._interval_tree = None

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
            annotations = [ x for x in self.iter_annotations() ]
            self._annotations = concatenate_annotations(annotations)
            return self._annotations
        else:
            return self._annotations

    @property
    def interval_tree(self):
        if not self._interval_tree:
            self._interval_tree = GateIntervalTree()
            return self._interval_tree
        else:
            return self._interval_tree

    def iter_annotations(self):
        annotations = self.root.iterfind(
            ".//Annotation"
        )
        for x in annotations:
            yield Annotation(x, self)

    def save_changes(self,
                     file_path=None):
        if not file_path:
            file_path = self.filename

        self.tree.write(
            file_path,
            pretty_print=True,
            xml_declaration=True,
        )


class GateIntervalTree:
    def __init__(self):
        self._tree = intervaltree.IntervalTree()

    def __iter__(self):
        for x in self._tree:
            yield x.data

    def add(self,
            annotation):
        self._tree.addi(
            annotation.start_node,
            annotation.end_node,
            annotation,
        )

    def search(self,
               annotation):
        return list(
            itertools.chain.from_iterable(
                [
                    [
                        match.data
                        for match in self._tree.search(
                            annotation_span.start_node,
                            annotation_span.end_node,
                        )
                    ]
                    for annotation_span
                    in annotation.spans
                ]
            )
        )

class Annotation:
    def __init__(self,
                 annotation_element,
                 annotation_file):
        self._annotation_element = annotation_element
        self._annotation_file = annotation_file
        self._type = annotation_element.get("Type")
        self._id = annotation_element.get("Id")
        self._start_node = int(annotation_element.get("StartNode"))
        self._end_node = int(annotation_element.get("EndNode"))
        self._continuations = []
        self._features = {}
        self.previous = None
        self.next = None

        annotation_set_name = self._annotation_element.getparent().get("Name")
        if annotation_set_name:
            self._annotation_set_name = annotation_set_name
        else:
            self._annotation_set_name = ""

        if self._type == "Attribution":
            self._caused_event_id = None
            for name, feature in self.features.items():
                if name.lower() == "caused_event":
                    self._caused_event_id = feature.value.split()[0]
                    break

    @property
    def annotation_file(self):
        return self._annotation_file

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
        if not self._features:
            features = [
                Feature(x)
                for x in self._annotation_element
                if x.tag == "Feature"
            ]
            self._features = {
                feature.name : feature
                for feature in features
            }
            return self._features
        else:
            return self._features

    @property
    def annotation_set_name(self):
        return self._annotation_set_name

    @property
    def continuations(self):
        return self._continuations

    @property
    def spans(self):
        return list(
            itertools.chain( [self], ( x for x in self.continuations ) )
        )

    @property
    def text(self):
        return "".join(
            self.annotation_file.nodes[node].tail
            for node in sorted(
                self.char_set.intersection(
                    self.annotation_file.nodes.keys()
                )
            )
        )

    def get_concatenated_text(self,
                              separator=None):
        if not separator:
            separator = " "
        return separator.join(
            x.text for x in self.spans
        )

    @property
    def char_set(self):
        return frozenset(
            range(
                self.start_node,
                self.end_node
            )
        )

    @property
    def concatenated_char_set(self):
        if self.continuations:
            return reduce(
                lambda x,y : frozenset( x | y.char_set ),
                self.spans[1:],
                self.spans[0].char_set
            )
        else: return self.char_set

    def _add_continuation(self,
                          annotation):
        self._continuations.append(annotation)

    def remove_feature(self,
                       name):
        if name in self.features:
            feature_element = self.features[name]._feature_element
            self._annotation_element.remove(feature_element)
            del self.features[name]
        else:
            return

    def add_feature(self,
                    name,
                    value,
                    overwrite=False):
        if name in self.features:
            already_present = True
            if overwrite == False:
                return
        else:
            already_present = False

        def _add_element(feature_element, tag, string):
            element = feature_element.makeelement(
                tag,
                attrib={
                    "className" : "java.lang.String"
                }
            )
            element.text = string
            feature_element.append(element)

        feature_element = (
            self
            ._annotation_element
            .makeelement("Feature")
        )
        _add_element(feature_element, "Name", name)
        _add_element(feature_element, "Value", value)

        if already_present:
            self.remove_feature(name)

        self._annotation_element.append(feature_element)

        feature = Feature(feature_element)

        self._features.update(
            { feature.name : feature }
        )

class Feature:
    def __init__(self, feature_element):
        self._feature_element = feature_element
        self._name = None
        self._value = None

    @property
    def name(self):
        if not self._name:
            self._name = self._feature_element.find("./Name")
            return self._name.text
        else:
            return self._name.text
        # self._value = feature.find("./Value")

    @name.setter
    def name(self, name):
        self._name.text = name

    @property
    def value(self):
        if self._value is None:
            self._value = self._feature_element.find("./Value")
            return self._value.text
        else:
            return self._value.text

    @value.setter
    def value(self, value):
        self._value.text = value

    def tally(self):
        self.value = str(int(self.value) + 1)

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

def dlink(annotations):
    sorted_annotations = sorted(
        sorted(
            annotations,
            key=lambda x: x.start_node,
        ),
        key=lambda x: x.end_node,
    )
    for i, annotation in enumerate(sorted_annotations[:-1]):
        annotation.previous = sorted_annotations[ i-1 ]
        annotation.next = sorted_annotations[ i+1 ]
    sorted_annotations[0].previous = None
    sorted_annotations[-1].previous = sorted_annotations[-2]

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
            continued_annotation._add_continuation(annotation)

    return [
        annotation
        for annotation in annotations
        if not annotation.type.endswith("_continuation")
    ]

def is_overlapping(annotations):
    if len(annotations) == 0:
        raise Exception("Can't compare to nothing!")
    return all(
        not (
            annotation
            .concatenated_char_set
            .isdisjoint(
                annotations[i+1]
                .concatenated_char_set
            )
        )
        for i, annotation in enumerate( annotations[:-1] )
    )
