#!/usr/bin/env python3

from functools import reduce
from collections import OrderedDict
import itertools
from lxml import etree
from bisect import bisect_left
import intervaltree

from . import diff
from . import turn_parser


class AnnotationFile:
    def __init__(self, filename):
        self._filename = filename
        self._tree = etree.parse(self.filename)
        self._root = self.tree.getroot()
        self._nodes = None
        self.__nodes_list = []
        self._text_with_nodes = None
        self._annotation_sets = []
        self._annotation_sets_dict = {}
        self._annotations = []
        self._interval_tree = None

    def __repr__(self):
        return "AnnotationFile('{}')".format(self.filename)

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

    @text.setter
    def text(self,
             new_text):
        self.text_with_nodes.clear()
        new_zero_node = self.text_with_nodes.makeelement("Node")
        new_zero_node.set("id", "0")
        new_zero_node.tail = new_text
        self.text_with_nodes.append(new_zero_node)
        self.nodes.update({ 0 : new_zero_node })
        self._nodes_list.append(0)

    @property
    def nodes(self):
        if not self._nodes:
            nodes = self.text_with_nodes.getchildren()
            self._nodes = { int(node.get("id")) : node for node in nodes }
            return self._nodes
        else:
            return self._nodes

    @property
    def _nodes_list(self):
        if not self.__nodes_list:
            self.__nodes_list = sorted(list(self.nodes.keys()))
        return self.__nodes_list

    def insert_node(self, offset):
        left_neighbor_index = bisect_left(self._nodes_list, offset) - 1
        left_neighbor_offset = self._nodes_list[left_neighbor_index]
        left_neighbor_element = self.nodes[left_neighbor_offset]

        assert offset >= left_neighbor_offset

        new_node_tail = left_neighbor_element.tail[
            (offset - left_neighbor_offset):
        ]
        left_neighbor_element.tail = left_neighbor_element.tail[
            :(offset - left_neighbor_offset)
        ]

        new_node_element = left_neighbor_element.makeelement(
            "Node",
            attrib={"id":str(offset)}
        )
        new_node_element.tail = new_node_tail

        self.text_with_nodes.insert(
            self.text_with_nodes.index(left_neighbor_element) + 1,
            new_node_element,
        )

        self._nodes_list.insert(left_neighbor_index + 1, offset)
        self.nodes.update({ offset : new_node_element })

    @property
    def text_with_nodes(self):
        if self._text_with_nodes is None:
            self._text_with_nodes = self.root.find(".//TextWithNodes")
            return self._text_with_nodes
        else:
            return self._text_with_nodes

    @property
    def annotation_set_names(self):
        return [
            annotation_set.name
            for annotation_set in self.annotation_sets
        ]

    @property
    def annotations(self):
        if not self._annotations:
            self._annotations = [ x for x in self.iter_annotations() ]
        return self._annotations

    @property
    def interval_tree(self):
        if not self._interval_tree:
            self._interval_tree = GateIntervalTree()
        return self._interval_tree

    def iter_annotations(self):
        annotations = itertools.chain.from_iterable(
            annotation_set.annotations
            if annotation_set.annotations
            else annotation_set.iter_annotations()
            for annotation_set in self.annotation_sets
        )
        for annotation in annotations:
            yield annotation

    def save_changes(self,
                     file_path=None):
        if not file_path:
            file_path = self.filename

        self.tree.write(
            file_path,
            pretty_print=True,
            xml_declaration=True,
        )

    @property
    def annotation_sets(self):
        if not self._annotation_sets:
            annotation_set_elements = self.root.findall("./AnnotationSet")
            self._annotation_sets = [
                AnnotationSet(x, self)
                for x in annotation_set_elements
            ]
        return self._annotation_sets

    @property
    def annotation_sets_dict(self):
        if not self._annotation_sets_dict:
            self._annotation_sets_dict = {
                annotation_set.name : annotation_set
                for annotation_set in self.annotation_sets
            }
        return self._annotation_sets_dict

    def create_annotation_set(self,
                              name=None):
        if name in self.annotation_set_names:
            return
        else:
            annotation_set_element = self.root.makeelement(
                "AnnotationSet",
                attrib={
                    "Name": name,
                }
            )
            annotation_set = AnnotationSet(annotation_set_element, self)

            self.root.append(annotation_set_element)
            self.annotation_sets.append(annotation_set)
            self.annotation_sets_dict.update(
                {annotation_set.name : annotation_set}
            )
        return annotation_set

class AnnotationSet:
    def __init__(self,
                 annotation_set_element,
                 annotation_file):
        self._element = annotation_set_element
        self._annotation_file = annotation_file
        self._name = self._element.get("Name")
        if not self._name:
            self._name = ""
        self._max_id = None
        self._annotations = []
        self._annotation_types = set()

    def __str__(self):
        return ", ".join(
            [
                "name: '{}'".format(self._name),
                "annotation_file: '{}'".format(self.annotation_file.filename),
                "annotation_types : {}".format(self.annotation_types),
                "number of annotations: {}".format(len(self.annotations)),
            ]
        )

    def __iter__(self):
        return iter(self.annotations)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        self._element.set("Name", new_name)
        self._name = new_name

    @property
    def annotation_file(self):
        return self._annotation_file

    @property
    def max_id(self):
        if not self._max_id:
            if self._annotations:
                annotations = self.annotations
            else:
                annotations = self.iter_annotations()
            try:
                self._max_id = str(
                    max(
                        int(annotation.id)
                        for annotation in annotations
                    )
                )
            except ValueError:
                self._max_id = None
        return self._max_id

    @property
    def annotations(self):
        if not self._annotations:
            annotations = [ x for x in self.iter_annotations() ]
            self._annotations = concatenate_annotations(annotations)
            return self._annotations
        else:
            return self._annotations

    def iter_annotations(self):
        annotations = self._element.iterfind(
            "./Annotation"
        )
        for x in annotations:
            yield Annotation(x, self)

    @property
    def annotation_types(self):
        if not self._annotation_types:
            self._annotation_types = set(
                annotation.type
                for annotation in self.iter_annotations()
            )
        return self._annotation_types

    def create_annotation(self,
                          annotation_type,
                          start,
                          end,
                          feature_dict=None):
        if self.max_id:
            annotation_id = str(int(self.max_id) + 1)
            self._max_id += 1
        else:
            annotation_id = str(1)
            self._max_id = 1

        annotation_element = self._element.makeelement(
            "Annotation",
            attrib={
                "Type": annotation_type,
                "Id": annotation_id,
                "StartNode": str(start),
                "EndNode": str(end),
            }
        )
        annotation = Annotation(annotation_element, self)
        if feature_dict:
            for name, value in feature_dict.items():
                annotation.add_feature(name, value)

        ###
        # for offset in [start, end]:
        #     if offset not in self.annotation_file.nodes:
        #         self.annotation_file.add_node(offset)
        ###

        self._element.append(annotation_element)
        if self._annotations:
            self._annotations.append(annotation)

        return annotation

    def append(self, annotation):
        self._element.append(annotation._element)
        if self._annotations:
            self._annotations.append(annotation)

    def delete(self):
        self.annotation_file.root.remove(self._element)
        self.annotation_file.annotation_sets.remove(self)
        del self.annotation_file.annotation_sets_dict[self.name]


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
                 annotation_set):
        self._element = annotation_element
        self._annotation_set = annotation_set
        self._type = annotation_element.get("Type")
        self._id = annotation_element.get("Id")
        self._start_node = int(annotation_element.get("StartNode"))
        self._end_node = int(annotation_element.get("EndNode"))
        self._continuations = []
        self._features = {}
        self._turn = None
        self.previous = None
        self.next = None

        if self._type == "Attribution":
            self._caused_event_id = None
            for name, feature in self.features.items():
                if name.lower() == "caused_event":
                    self._caused_event_id = feature.value.split()[0]
                    break

    def __str__(self):
        id_string = "id: {}".format(self.id)
        type_string = "type: {}".format(self.type)
        start_node_string = "start_node: {}".format(self.start_node)
        end_node_string = "end_node: {}".format(self.end_node)
        text_string = 'text: """{}"""'.format(self.text)
        features_string_dict = {
            k: v.value
            for k, v in self.features.items()
        }
        features_string = 'features: {}'.format(features_string_dict)

        return ", ".join(
            [
                id_string,
                type_string,
                start_node_string,
                end_node_string,
                text_string,
                features_string,
            ]
        )

    def __repr__(self):
        return "{}({}, {})".format(
            self.__class__.__name__,
            self._element,
            self._annotation_set,
        )

    def __len__(self):
        return self.end_node - self.start_node

    def delete(self):
        unlink(self)
        self.annotation_set._element.remove(self._element)

    @property
    def annotation_set(self):
        return self._annotation_set

    @property
    def annotation_file(self):
        return self.annotation_set.annotation_file

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

    @start_node.setter
    def start_node(self, start_node):
        self._element.set("StartNode", str(start_node))
        self._start_node = start_node

    @end_node.setter
    def end_node(self, end_node):
        self._element.set("EndNode", str(end_node))
        self._end_node = end_node

    @property
    def turn(self):
        return self._turn

    @turn.setter
    def turn(self, turn):
        self._turn = turn

    @property
    def features(self):
        if not self._features:
            features = [
                Feature(x)
                for x in self._element
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
            self._element.remove(feature_element)
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
            ._element
            .makeelement("Feature")
        )
        _add_element(feature_element, "Name", name)
        _add_element(feature_element, "Value", value)

        if already_present:
            self.remove_feature(name)

        self._element.append(feature_element)

        feature = Feature(feature_element)

        self._features.update(
            { feature.name : feature }
        )

class Feature:
    def __init__(self, feature_element):
        self._feature_element = feature_element
        self._name = None
        self._value = None

    def __str__(self):
        return "name: '{}', value: '{}'".format(self.name, self.value)

    def __repr__(self):
        return "Feature({})".format(self._feature_element)

    @property
    def name(self):
        if self._name is None:
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
    for i, annotation in enumerate(annotations[:-1]):
        annotation.previous = annotations[ i-1 ]
        annotation.next = annotations[ i+1 ]
    annotations[0].previous = None
    annotations[-1].previous = annotations[-2]

def unlink(annotation):
    # if surrounded
    if annotation.previous and annotation.next:
        annotation.previous.next = annotation.next
        annotation.next.previous = annotation.previous
    # if right edge
    elif annotation.previous:
        annotation.previous.next = None
    # if left edge
    elif annotation.next:
        annotation.next.previous = None

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
            key=(lambda x: x.annotation_set.name)
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