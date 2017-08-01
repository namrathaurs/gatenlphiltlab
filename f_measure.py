def is_strict_match( x, y ):
    return x.get_char_set() == y.get_char_set()

def is_lenient_match( x, y ):
    """x and y must be sets"""
    return not x.get_char_set().isdisjoint(y.get_char_set())

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

    import gate

    paths = [
        "/home/nick/hilt/PES/8/4-MG-2014-05-16_PES_2_NB.xml",
        "/home/nick/hilt/PES/8/4-MG-2014-05-16_PES_2_NU.xml"
    ]

    sets = []

    for path in paths:
        annotation_file = gate.AnnotationFile(path)
        annotations = gate.AnnotationGroup(
            x for x in annotation_file.iter_annotations()
        ).get_annotations()
        spans = []
        for x in annotations:
            if x._type == "Attribution":
                spans.append(x)
        sets.append(spans)

    key_set = sets[0]
    response_set = sets[1]
    is_match = is_lenient_match

    print(
        calc_f_measure(
            key_set,
            response_set,
            (lambda x,y : is_match(x,y) and x._caused_event_id == y._caused_event_id )
        )
    )

if __name__ == "__main__":
    main()
