#!/usr/bin/env python3

import gatenlp
from collections import namedtuple
from collections import OrderedDict
from bisect import bisect_left
import difflib


def get_change_list(text1,
                    text2):
    seq = difflib.SequenceMatcher(None, text1, text2).get_opcodes()
    ordered_seq = sorted(seq, key=lambda x: x[1])
    diff = difflib.ndiff(text1,text2)

    change_list = OrderedDict({0:0})
    for tag, i1, i2, j1, j2 in ordered_seq:
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

        change_list.update(
            { key_char_pos : difference }
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
    for char_pos, change in change_list.items():
        accumulated_change = accumulated_change + change
        accumulated_changes.append(
            change_record(char_pos, accumulated_change)
        )

    return accumulated_changes

def align_annotations(annotations,
                      change_list):
    change_list_keys = [ x for x,_ in change_list ]
    for annotation in sorted(annotations, key=lambda x: x.start_node):

        # using start_node setter
        change_index = bisect_left(change_list_keys, annotation.start_node) - 1
        change = change_list[change_index]
        annotation.start_node = annotation.start_node + change.accumulated_change
        del change_list[:change_index]
        del change_list_keys[:change_index]

        # using end_node setter
        change_index = bisect_left(change_list_keys, annotation.end_node) - 1
        change = change_list[change_index]
        annotation.end_node = annotation.end_node + change.accumulated_change
        del change_list[:change_index]
        del change_list_keys[:change_index]

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


if __name__ == "__main__":

    pass

    annotation_file1_path = "/home/nick/test/diff/test_file1.xml"
    annotation_file2_path = "/home/nick/test/diff/test_file2.xml"

    annotation_file1 = gatenlp.AnnotationFile(annotation_file1_path)
    annotation_file2 = gatenlp.AnnotationFile(annotation_file2_path)

    annotations = sorted(
        [
            annotation
            for annotation in annotation_file1.annotations
            if annotation.type.lower() == "event"
        ],
        key=lambda x: x.start_node,
    )

    change_list = get_change_list(annotation_file1.text, annotation_file2.text)
    align_annotations(change_list, annotations)
    import_annotations(annotations, annotation_file2)

    # annotation_file2.save_changes()
