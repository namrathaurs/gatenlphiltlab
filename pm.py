import gate
test_f = "/home/nick/test/gate/pers_ment/11-JB_2015-07-12_PM_annotation.xml"
annotation_file = gate.AnnotationFile(test_f)
annotations = sorted(
    list( annotation_file.iter_annotations() ),
    key = lambda x : ( x._start_node, x._end_node )
)

for i, annotation in enumerate(annotations):
    if annotation._type.lower() == "token":
        if gate.is_overlapping(
            [
                annotation,
                annotations[i-1],
            ]
        ):
            print(
                annotation._type,
                annotations[i-1]._type
            )
            #TODO: try optimizing iter_overlapping_annotations()
            ## use something like a focal search
            #TODO: implement BIO tagging
        # j = i
        # while True:
            # annotation_type = annotations[j]._type
            # print(annotation_type)
            # if annotation_type.lower() == "person":
                # print()
                # break
            # j = j - 1
