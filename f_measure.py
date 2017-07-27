def is_strict_match( x, y ):
    return x == y

def is_lenient_match( x, y ):
    return not x.isdisjoint( y )

def iter_true_positives( key_set, response_set, is_match ):
    return ( (x,y) for x in response_set for y in key_set if is_match(x,y) )

def iter_false_positives( key_set, response_set, is_match ):
    return ( (x,y) for x in response_set for y in key_set if not is_match(x,y) )

def iter_false_negatives( key_set, response_set, is_match ):
    return ( (x,y) for x in key_set for y in response_set if not is_match(x,y) )

def calc_precision( num_true_positives, num_false_positives ):
    try: return num_true_positives / ( num_true_positives + num_false_positives )
    except ZeroDivisionError: return 1

def calc_recall( num_true_positives, num_false_negatives ):
    try: return num_true_positives / ( num_true_positives + num_false_negatives )
    except ZeroDivisionError: return 1

def calc_harmonic_mean( x, y ):
    return 2 * ( ( x * y ) / ( x + y ) )

def calc_f_measure( num_true_positives, num_false_positives, num_false_negatives ):
    precision = calc_precision(
        num_true_positives,
        num_false_positives
    )
    recall = calc_recall(
        num_true_positives,
        num_false_negatives
    )
    try: return calc_harmonic_mean( precision, recall )
    except ZeroDivisionError: return 0

def main():
    key_annotations = get_annotations(key_annotation_set)
    response_annotations = get_annotations(response_annotation_set)

    key_set = get_annotation_spans(key_annotation_set)
    response_set = get_annotation_spans(response_annotation_set)

    num_true_positives = len( iter_true_positives( key_set, response_set ) )
    num_false_positives = len( iter_false_positives( key_set, response_set ) )
    num_false_negatives = len( iter_false_negatives( key_set, response_set ) )

    precision = calc_precision( num_true_positives, num_false_positives ),
    recall = calc_recall( num_true_positives, num_false_negatives ),

    return calc_f_measure( precision, recall )

if __name__ == "__main__":
    main()
