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

    import argparse
    import gate


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
        "--annotation-file",
        dest="annotation_files",
        nargs=2,
        required="true",
        help="the input; a GATE annotation file with Person Mentions"
    )

    args = parser.parse_args()
    annotation_type = args.annotation_type
    paths = args.annotation_files

    annotations = []

    for path in paths:
        annotation_file = gate.AnnotationFile(path)
        annotations.append(
            [
                x for x in
                gate.AnnotationGroup(
                    y for y in annotation_file.iter_annotations()
                ).get_annotations()
                if x._type == annotation_type
            ]
        )

    key_annotations = annotations[0]
    response_annotations = annotations[1]

    def has_same_features(key, response):
        return any(
            x._name == y._name
            and x._value == y._value
            for x in response.get_features()
            for y in key.get_features()
        )

    does_span_match = is_lenient_match
    is_feature_match = True

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

    print(f_measure)

if __name__ == "__main__":
    main()
