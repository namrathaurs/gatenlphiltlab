#!/usr/bin/env python3

import gatenlphiltlab
from collections import namedtuple
from collections import OrderedDict
import itertools
import bisect
import difflib
import intervaltree
import Levenshtein


def get_change_tree(text1,
                     text2):
    change_tree = intervaltree.IntervalTree()
    # setting autojunk to True will greatly shorten processing time
    # at the expense of accuracy.
    seq = difflib.SequenceMatcher(None, text1, text2, autojunk=False)
    matching_blocks = seq.get_matching_blocks()
    for block in matching_blocks:
        difference = block.b - block.a
        if block.size != 0:
            change_tree.addi(
                block.a,
                block.a + block.size + 1,
                difference,
            )
    return change_tree

class ChangeTree():
    """
    An `interval tree <https://en.wikipedia.org/wiki/Interval_tree>`_ which
    stores the differences between *text1* and *text2*, optimizing for
    difference lookups for annotation offset reference corrections. All
    operations assume the changes inform how to get to *text2* from *text1*.

    Each interval in the tree corresponds to a text offset interval in *text1*,
    the data of which is an integer representing the change necessary to apply
    to any offsets in that interval in order to accurately refer to the same
    text within *text2*.

    Based on `intervaltree <https://pypi.python.org/pypi/intervaltree>`_.
    """
    def __init__(self,
                 text1,
                 text2):
        self._text1 = text1
        self._text2 = text2
        self._change_tree = get_change_tree(text1, text2)
        self._interval_tree_start_points = sorted(
            [
                interval.begin
                for interval in self._change_tree
            ]
        )
        self._interval_tree_end_points = sorted(
            [
                interval.end - 1
                for interval in self._change_tree
            ]
        )

    def get_lt_interval(self,
                        node):
        """
        Given *node*, return the nearest interval which contains nodes less than *node*.

        :rtype: `intervaltree.Interval <https://github.com/chaimleib/intervaltree/blob/master/intervaltree/interval.py>`_
        """
        nearest_lt_node = self._interval_tree_end_points[
            bisect.bisect_left(self._interval_tree_end_points, node) - 1
        ]
        nearest_lt_interval = sorted(
            self._change_tree[nearest_lt_node]
        )[0]
        return nearest_lt_interval

    def get_gt_interval(self,
                        node):
        """
        Given *node*, return the nearest interval which contains nodes greater than *node*.

        :rtype: `intervaltree.Interval <https://github.com/chaimleib/intervaltree/blob/master/intervaltree/interval.py>`_
        """
        nearest_gt_node = self._interval_tree_start_points[
            bisect.bisect_right(self._interval_tree_start_points, node)
        ]
        nearest_gt_interval = sorted(
            self._change_tree[nearest_gt_node]
        )[0]
        return nearest_gt_interval

    def get_changed_annotation_nodes(self,
                                     annotation):
        """
        Given an *annotation* with offsets referring to *text1*, return a new
        start node and end node that corresponds with the text in *text2*. If
        the text is not completely comparable, an estimation of the nearest
        text will be made using an algorithm incorporating `Levenshtein
        distances <https://en.wikipedia.org/wiki/Levenshtein_distance>`_.

        :param annotation: The annotation.
        :type annotation: :class:`gatenlphiltlab.Annotation`

        :returns: (start_node, end_node)
        :rtype: tuple(int, int)
        """
        possible_start_points = []
        possible_end_points = []

        for node in (annotation.start_node, annotation.end_node):
            try:
                interval = sorted(
                    self._change_tree[node]
                )[0]
                if node == annotation.start_node:
                    possible_start_points.append(
                        annotation.start_node
                        + interval.data
                    )
                elif node == annotation.end_node:
                    possible_end_points.append(
                        annotation.end_node
                        + interval.data
                    )
            except IndexError:
                nearest_lt_interval = self.get_lt_interval(node)
                nearest_gt_interval = self.get_gt_interval(node)
                if node == annotation.start_node:
                    possible_start_points.append(
                        annotation.start_node
                        + nearest_lt_interval.data
                    )
                    possible_start_points.append(
                        annotation.start_node
                        + nearest_gt_interval.data
                    )
                elif node == annotation.end_node:
                    possible_end_points.append(
                        annotation.end_node
                        + nearest_lt_interval.data
                    )
                    possible_end_points.append(
                        annotation.end_node
                        + nearest_gt_interval.data
                    )

        combinations = set(
            itertools.combinations(
                possible_start_points+possible_end_points, 2
            )
        )
        valid_combinations = [
            combination
            for combination in combinations
            if combination[0] < combination[1]
        ]

        longest_valid_combination = max(
            valid_combinations,
            key=lambda x: abs(x[1] - x[0])
        )

        intended_text = self._text1[
            annotation.start_node
            :annotation.end_node
        ]
        candidate_text = self._text2[
            longest_valid_combination[0]
            :longest_valid_combination[1]
        ]
        if len(intended_text) == len(candidate_text):
            new_start_node = longest_valid_combination[0]
            new_end_node = longest_valid_combination[1]
        else: 
            inner_tree = ChangeTree(candidate_text, intended_text)
            closest_pair = max(
                itertools.combinations(
                    inner_tree._interval_tree_start_points
                    + inner_tree._interval_tree_end_points,
                    2
                ),
                key=lambda x: Levenshtein.ratio(
                    self._text2[
                        longest_valid_combination[0] + x[0]
                        :longest_valid_combination[0] + x[1]
                    ],
                    intended_text
                ),
            )

            new_start_node = longest_valid_combination[0] + closest_pair[0]
            new_end_node = longest_valid_combination[0] + closest_pair[1]

        #TODO: fix id 1507 (etc.) and that one time where "have" wasn't annotated accurately
        new_text = self._text2[new_start_node:new_end_node]

        if new_text != intended_text:
            print(
                Levenshtein.ratio(new_text, intended_text),
                new_text,
                intended_text,
            )

        return (new_start_node, new_end_node)

def align_annotation(annotation,
                     change_tree):
    """
    Given an *annotation* and a *change_tree*, assuming that *annotation*
    corresponds to the same text as in *text1* of the *change_tree*, set
    *annotation*'s start and end nodes appropriately to refer to
    *change_tree*'s *text2*.

    :param annotation: The annotation to correct.
    :type annotation: :class:`gatenlphiltlab.Annotation`

    :param change_tree: The change tree to use for change lookups.
    :type change_tree: :class:`~gatenlphiltlab.diff.ChangeTree`
    """
    annotation.start_node, annotation.end_node = (
        change_tree.get_changed_annotation_nodes(annotation)
    )

def align_annotations(annotations,
                      change_tree):
    """
    :func:`align <gate.align_annotation>` each annotation in *annotations* according to *change_tree*.

    :param annotations: The annotations to correct.
    :type annotations: iterable of :class:`gatenlphiltlab.Annotation`

    :param change_tree: The change tree to use for change lookups.
    :type change_tree: :class:`~gatenlphiltlab.diff.ChangeTree`
    """
    for annotation in annotations:
        align_annotation(annotation, change_tree)

def assure_nodes(annotations,
                 annotation_file):
    """
    If any node references within *annotations* are not yet present within *annotation_file*, create them.

    :param annotations: The annotations.
    :type annotations: iterable of :class:`gatenlphiltlab.Annotation`

    :param annotation_file: The annotation file.
    :type annotation_file: :class:`gatenlphiltlab.AnnotationFile`
    """
    for annotation in annotations:
        start_node = annotation.start_node
        end_node = annotation.end_node
        for node in [start_node, end_node]:
            if node not in annotation_file.nodes:
                try:
                    annotation_file.insert_node(node)
                except AssertionError:
                    print(
                        node,
                        max(annotation_file.nodes.keys())
                    )

def import_annotations(annotations,
                       annotation_file):
    """
    Create annotations for all *annotations* which don't exist in *annotation_file*.

    :param annotations: The annotations to import.
    :type annotations: iterable of :class:`gatenlphiltlab.Annotation`

    :param annotation_file: The annotation file.
    :type annotation_file: :class:`gatenlphiltlab.AnnotationFile`
    """
    destination_annotations = set(annotation_file.annotations)
    for annotation in annotations:
        annotation_set_name = annotation.annotation_set.name
        if annotation_set_name not in annotation_file.annotation_set_names:
            annotation_file.create_annotation_set(
                annotation_set_name
            )
        target_annotation_set = (
            annotation_file
            .annotation_sets_dict[
                annotation_set_name
            ]
        )
        if annotation not in target_annotation_set.annotations:
            target_annotation_set.create_annotation(
                annotation.type,
                annotation.start_node,
                annotation.end_node,
                feature_dict={
                    feature.name: feature.value
                    for feature in
                    annotation.features.values()
                },
            )
