#!/usr/bin/env python3

import gatenlp
from collections import namedtuple
from collections import OrderedDict
import itertools
import bisect
import difflib
import intervaltree
import Levenshtein


def _get_change_tree(text1,
                     text2):
    change_tree = intervaltree.IntervalTree()
    seq = difflib.SequenceMatcher(None, text1, text2, autojunk=False)
    # seq = difflib.SequenceMatcher(None, text1, text2,)
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
    def __init__(self,
                 text1,
                 text2):
        self._text1 = text1
        self._text2 = text2
        self._change_tree = _get_change_tree(text1, text2)
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
        nearest_lt_node = self._interval_tree_end_points[
            bisect.bisect_left(self._interval_tree_end_points, node) - 1
        ]
        nearest_lt_interval = sorted(
            self._change_tree.search(nearest_lt_node)
        )[0]
        return nearest_lt_interval

    def get_gt_interval(self,
                        node):
        nearest_gt_node = self._interval_tree_start_points[
            bisect.bisect_right(self._interval_tree_start_points, node)
        ]
        nearest_gt_interval = sorted(
            self._change_tree.search(nearest_gt_node)
        )[0]
        return nearest_gt_interval

    def get_changed_annotation_nodes(self,
                                     annotation):
        possible_start_points = []
        possible_end_points = []

        for node in (annotation.start_node, annotation.end_node):
            try:
                interval = sorted(
                    self._change_tree.search(node)
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
    annotation.start_node, annotation.end_node = (
        change_tree.get_changed_annotation_nodes(annotation)
    )

def align_annotations(annotations,
                      change_tree):
    for annotation in annotations:
        align_annotation(annotation, change_tree)

def assure_nodes(annotations,
                 annotation_file):
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
