def get_annotation_spans( annotations ):
    return ( span for get_caused_event( annotation ), get_annotation_span( annotation ) in annotations )

def iter_true_positives( key_set, response_set ):
    return ( x for x in response_set if x in key_set )

def iter_false_positives( key_set, response_set ):
    return ( x for x in response_set if x not in key_set )

def iter_false_negatives( key_set, response_set ):
    return ( x for x in key_set if x in response_set )

def calc_precision( num_true_positives, num_false_positives ):
    return num_true_positives / ( num_true_positives + num_false_positives )

def calc_recall( num_true_positives, num_false_negatives ):
    return num_true_positives / ( num_true_positives + num_false_negatives )

def calc_harmonic_mean( x, y ):
    return 2 * ( ( x * y ) / ( x + y ) )

def calc_f_measure( precision, recall ):
    return harmonic_mean( precision, recall )

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
