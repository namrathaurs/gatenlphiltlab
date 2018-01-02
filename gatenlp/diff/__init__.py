#!/usr/bin/env python3

import gatenlp
from collections import namedtuple
from collections import OrderedDict
from bisect import bisect_right
import difflib
import intervaltree


def get_change_tree(text1,
                    text2):
    change_tree = intervaltree.IntervalTree()
    seq = difflib.SequenceMatcher(None, text1, text2)
    matching_blocks = seq.get_matching_blocks()
    for block in matching_blocks:
        difference = block.b - block.a
        if block.size != 0:
            change_tree.addi(
                block.a,
                block.a + block.size,
                difference,
            )

    return change_tree

def align_annotations(annotations,
                      change_tree):
    interval_end_points = sorted(
        [
            interval.end
            for interval in change_tree
        ]
    )
    for annotation in annotations:
        start_node = annotation.start_node
        end_node = annotation.end_node
        changes = []
        for node in (start_node, end_node):
            try:
                interval = sorted(
                    change_tree.search(node)
                )[0]
            except IndexError:
                nearest_node = interval_end_points[
                    bisect_right(interval_end_points, node) - 1
                ]
                nearest_le_interval = sorted(
                    change_tree.search(
                        nearest_node - 1
                    )
                )[0]
                interval = nearest_le_interval
            change = interval.data
            changes.append(change)

        annotation.start_node = annotation.start_node + changes[0]
        annotation.end_node = annotation.end_node + changes[1]


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
