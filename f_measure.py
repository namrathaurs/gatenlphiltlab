#!/usr/bin/env python3

def is_strict_match( x, y ):
    return x == y

def is_lenient_match( x, y ):
    """x and y must be sets"""
    return not x.isdisjoint(y)

def iter_true_positives(key_set,
                        response_set,
                        is_match):
    """"key_set and response_set must be a list of frozensets.
    is_match must be a boolean expression.
    """
    return (
        response
        for response in response_set
        if any(
            ( is_match(response, key) for key in key_set )
        )
    )

def iter_false_positives(key_set,
                         response_set,
                         is_match):
    """key_set and response_set must be a list of frozensets.
    is_match must be a boolean expression.
    """
    return (
        response
        for response in response_set
        if not any(
            ( is_match(response, key) for key in key_set )
        )
    )

def iter_false_negatives(key_set,
                         response_set,
                         is_match):
    """key_set and response_set must be a list of frozensets.
    is_match must be a boolean expression.
    """
    return (
        key
        for key in key_set
        if not any(
            ( is_match(key, response) for response in response_set )
        )
    )

def calc_precision(num_true_positives,
                   num_false_positives):
    try:
        return (
            ( num_true_positives ) /
            ( num_true_positives + num_false_positives )
        )
    except ZeroDivisionError:
        # Since dividing by zero only happens when both annot-
        # ators select nothing, evaluate this as perfect agree-
        # ment.
        return 1

def calc_recall(num_true_positives,
                num_false_negatives):
    try:
        return (
            ( num_true_positives ) /
            ( num_true_positives + num_false_negatives )
        )
    except ZeroDivisionError:
        # Since dividing by zero only happens when both annot-
        # ators select nothing, evaluate this as perfect agree-
        # ment.
        return 1

def calc_harmonic_mean( x, y ):
    return 2 * ( ( x * y ) / ( x + y ) )

def calc_f_measure(key_set,
                   response_set,
                   is_match):


    num_true_positives = sum(
        1 for _ in iter_true_positives( key_set, response_set, is_match )
    )
    num_false_positives = sum(
        1 for _ in iter_false_positives( key_set, response_set, is_match )
    )
    num_false_negatives = sum(
        1 for _ in iter_false_negatives(key_set, response_set, is_match)
    )

    precision = calc_precision(
        num_true_positives,
        num_false_positives
    )
    recall = calc_recall(
        num_true_positives,
        num_false_negatives
    )

    try:
        return calc_harmonic_mean( precision, recall )
    except ZeroDivisionError:
        # Since division by zero will only happen when
        # no true-positives are selected, evaluate as
        # no agreement.
        return 0

def main():

    from itertools import product
    import argparse
    import gate

    class InputError(Exception):
        pass

    parser = argparse.ArgumentParser(
        description="Computes inter-rater reliability of like "
        "annotations between two annotation files in terms "
        "of an F1 score.",
    )
    parser.add_argument(
        "-t",
        "--annotation-type",
        dest="annotation_type",
        required="true",
        help="the type of annotation that will be compared"
    )
    parser.add_argument(
        "-f",
        action="store_true",
        dest="feature_match",
        default=False,
        help="use features as part of match function"
    )
    parser.add_argument(
        "-s",
        "--strict",
        action="store_true",
        dest="strict",
        default=False,
        help="use strict span-matching, i.e. identical spans"
    )
    parser.add_argument(
        "-l",
        "--lenient",
        action="store_true",
        dest="lenient",
        default=False,
        help="use lenient span-matching, i.e. overlapping spans"
    )
    parser.add_argument(
        "-p",
        "--pes-mode",
        action="store_true",
        dest="pes_mode",
        default=False,
        help="temporary PES mode which evaluates only those attributions "
        "for which the events are universally considered valid"
    )
    parser.add_argument(
        "-i",
        "--annotation-files",
        dest="annotation_file",
        nargs=2,
        required="true",
        help="GATE annotation files"
    )

    args = parser.parse_args()
    annotation_type = args.annotation_type
    paths = args.annotation_file
    lenient = args.lenient
    strict = args.strict
    is_feature_match = args.feature_match

    if strict and lenient:
        raise InputError(
            "F-measure can't be both lenient and strict!"
        )
    if not ( strict or lenient ):
        raise InputError(
            "Must choose either strict or lenient!"
        )

    annotations = []
    for path in paths:
        annotation_file = gate.AnnotationFile(path)
        annotations.append(
            [
                x for x in
                gate.AnnotationGroup(
                    y for y in annotation_file.iter_annotations()
                ).get_annotations()
                if (x._type == annotation_type)
                or (x._type == "Event")
            ]
        )
    key_annotations = [
        x for x in
        annotations[0]
        if x._type == annotation_type
    ]
    response_annotations = [
        x for x in
        annotations[1]
        if x._type == annotation_type
    ]
    key_event_annotations = [
        x for x in
        annotations[0]
        if x._type == "Event"
    ]
    response_event_annotations = [
        x for x in
        annotations[1]
        if x._type == "Event"
    ]

    def has_same_features(key, response):
        return all(
            x._value == y._value
            for x,y
            in zip(
                sorted(
                    ( x for x in response.get_features() ),
                    key=lambda x: x._name
                ),
                sorted(
                    ( x for x in key.get_features() ),
                    key=lambda x: x._name
                )
            )
        )

    ### only when agreed on event validity
    if args.pes_mode:
        if not any(
            x._caused_event_id == y._caused_event_id
            and any(
                (
                    a._name == "has_valid_attribute"
                    and
                    b._name == "has_valid_attribute"
                    and
                    a._value == "yes"
                    and
                    b._value == "yes"
                )
                for a,b in product(
                    x.get_caused_event(response_event_annotations).get_features(),
                    y.get_caused_event(key_event_annotations).get_features()
                )
            )
            for x,y in product(key_annotations, response_annotations)
        ):
            print("0.0")
            quit()
        key_annotations = [
            x for x in filter(
                lambda x: any(
                    x._caused_event_id == y._caused_event_id
                    and any(
                        (
                            a._name == "has_valid_attribute"
                            and
                            b._name == "has_valid_attribute"
                            and
                            a._value == "yes"
                            and
                            b._value == "yes"
                        )
                        for a,b in product(
                            x.get_caused_event(key_event_annotations).get_features(),
                            y.get_caused_event(response_event_annotations).get_features()
                        )
                    )
                    for y in response_annotations
                ),
                key_annotations
            )
        ]
        response_annotations = [
            x for x in filter(
                lambda x: any(
                    x._caused_event_id == y._caused_event_id
                    and any(
                        (
                            a._name == "has_valid_attribute"
                            and
                            b._name == "has_valid_attribute"
                            and
                            a._value == "yes"
                            and
                            b._value == "yes"
                        )
                        for a,b in product(
                            x.get_caused_event(response_event_annotations).get_features(),
                            y.get_caused_event(key_event_annotations).get_features()
                        )
                    )
                    for y in key_annotations
                ),
                response_annotations
            )
        ]
    ### end agreed event filter

    if strict:
        does_span_match = is_strict_match
    if lenient:
        does_span_match = is_lenient_match

    def is_match(x,y):
        span_match = does_span_match(
            x.get_concatenated_char_set(),
            y.get_concatenated_char_set()
        )
        if is_feature_match:
            feature_match = has_same_features(x,y)
            return span_match and feature_match
        else: return span_match

    f_measure = calc_f_measure(
        key_annotations,
        response_annotations,
        is_match
    )

    print(
        round(
            f_measure,
            4
        )
    )

if __name__ == "__main__":
    main()
