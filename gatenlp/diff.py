#!/usr/bin/env python3

import gatenlp
from collections import namedtuple
from collections import OrderedDict
from bisect import bisect_right
import difflib
import intervaltree


def get_change_list(text1,
                    text2):
    # seq = difflib.SequenceMatcher(None, text1, text2).get_opcodes()
    seq = difflib.SequenceMatcher(None, text1, text2)

    for x in seq.get_matching_blocks():
        print(repr(x))
    quit()

    # for x in difflib.ndiff(text1, text2):
        # print(repr(x))

    change_list = []
    for tag, i1, i2, j1, j2 in seq:
        if tag == "equal":
            continue
        elif tag == "delete":
            key_char_pos = i1
            difference = i1 - i2
        elif tag == "insert":
            key_char_pos = i1
            difference = j2 - j1
        elif tag == "replace":
            key_char_pos = i2
            difference = (j2 - j1) - (i2 - i1)

        change_list.append(
            ( key_char_pos, difference )
        )

    change_record = namedtuple(
        "change_record",
        [
            "char_pos",
            "accumulated_change"
        ]
    )
    accumulated_changes = []
    accumulated_change = 0
    for char_pos, change in sorted(change_list, key=lambda x: x[0]):
        accumulated_change = accumulated_change + change
        accumulated_changes.append(
            change_record(char_pos, accumulated_change)
        )

    # return sorted(accumulated_changes, key=lambda x: x.char_pos)
    return accumulated_changes

def get_change_list_2(text1,
                      text2):
    change_record = namedtuple(
        "change_record",
        [
            "char_pos",
            "accumulated_change"
        ]
    )

    # seq = difflib.SequenceMatcher(None, text1, text2, autojunk=False)
    seq = difflib.SequenceMatcher(None, text1, text2)
    matching_blocks = seq.get_matching_blocks()
    interval_tree = intervaltree.IntervalTree()
    for block in matching_blocks:
        difference = block.b - block.a
        if block.size != 0:
            interval_tree.addi(
                block.a,
                block.a + block.size,
                difference,
            )

    return interval_tree

def align_annotations(annotations,
                      change_list):
    change_list_keys = [ x.char_pos for x in change_list ]
    for annotation in annotations:

        # using start_node setter
        change_index = bisect_right(change_list_keys, annotation.start_node) - 1
        if change_index < 0: change_index = 0
        change = change_list[change_index]
        annotation.start_node = annotation.start_node + change.accumulated_change

        # using end_node setter
        change_index = bisect_right(change_list_keys, annotation.end_node) - 1
        if change_index < 0: change_index = 0
        change = change_list[change_index]
        annotation.end_node = annotation.end_node + change.accumulated_change

def align_annotations_2(annotations,
                        interval_tree):
    interval_end_points = sorted(
        [
            interval.end
            for interval in interval_tree
        ]
    )
    for annotation in annotations:
        start_node = annotation.start_node
        end_node = annotation.end_node
        changes = []
        for node in (start_node, end_node):
            try:
                interval = sorted(
                    interval_tree.search(node)
                )[0]
            # interval = next(
                # (
                    # x for x in interval_tree.search(node)
                # ),
                # None
            # )
            # if not interval:
            except IndexError:
                nearest_node = interval_end_points[
                    bisect_right(interval_end_points, node) - 1
                ]
                nearest_le_interval = sorted(
                    interval_tree.search(
                        nearest_node - 1
                    )
                )[0]
                # nearest_le_interval = next(
                    # x for x in interval_tree.search(
                        # nearest_node - 1
                    # )
                # )
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
                annotation_file.insert_node(node)

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
