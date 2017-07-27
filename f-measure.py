def get_key_set():

def get_response_set():

def get_true_positives( key_set, response_set ):
    return [ x for x in response_set if x in key_set ]

def get_false_positives( key_set, response_set ):
    return [ x for x in response_set if x not in key_set ]

def get_false_negatives( key_set, response_set ):
    return [ x for x in key_set if x in response_set ]

def calc_precision( num_true_positives, num_false_positives ):
    return num_true_positives / ( num_true_positives + num_false_positives )

def calc_recall( num_true_positives, num_false_negatives ):
    return num_true_positives / ( num_true_positives + num_false_negatives )

def calc_harmonic_mean( x, y ):
    return 2 * ( ( x * y ) / ( x + y ) )

def calc_f_measure( precision, recall ):
    return harmonic_mean( precision, recall )

key_set = get_key_set()
response_set = get_response_set()

true_positives = get_true_positives( key_set, response_set )
false_positives = get_false_positives( key_set, response_set )
false_negatives = get_false_negatives( key_set, response_set )

num_true_positives = len( true_positives )
num_false_positives = len( false_positives )
num_false_negatives = len( false_negatives )

precision = calc_precision( num_true_positives, num_false_positives ),
recall = calc_recall( num_true_positives, num_false_negatives ),

calc_f_measure( precision, recall )
