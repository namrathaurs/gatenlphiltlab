import numpy as np


def cronbachs_alpha(annotations):
    item_scores = np.asarray(annotations)
    item_variances = item_scores.var(axis=1, ddof=1)
    total_scores = item_scores.sum(axis=0)
    num_items = len(item_scores)

    return (
        ( num_items / (num_items - 1.) )
        * ( 1 - item_variances.sum() / total_scores.var(ddof=1) )
    )

def main():

    import argparse
    import gate


    parser = argparse.ArgumentParser(
        description="Computes inter-rater reliability of like "
        "annotations between two annotation files in terms "
        "of Cronbach's Alpha.",
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
    paths = args.annotation_file

    annotation_files = (
        gate.AnnotationFile(path)
        for path in paths
    )

    annotations = [
        x for x in zip(
            *[
                sorted(
                    (
                        x for x in gate.AnnotationGroup(
                            y for y in annotation_file.iter_annotations()
                        ).get_annotations()
                        if (x._type == "Attribution")
                    ),
                    key=lambda x: x._id
                )
                for annotation_file in annotation_files
            ]
        )
    ]

    def get_value_by_name(name, annotation):
        return next(
            int(annotation._value.split(" ")[0])
            for annotation in annotation.get_features()
            if name in annotation._name.lower()
        )

    annotations_internality = [
        (
            get_value_by_name("pers", x),
            get_value_by_name("pers", y),
        )
        for x, y in annotations
    ]
    annotations_stability = [
        (
            get_value_by_name("perm", x),
            get_value_by_name("perm", y),
        )
        for x, y in annotations
    ]
    annotations_globality = [
        (
            get_value_by_name("perv", x),
            get_value_by_name("perv", y),
        )
        for x, y in annotations
    ]

    print(annotations_internality)
    print(np.asarray(annotations_internality))
    print(cronbachs_alpha(annotations_internality))
    print(np.corrcoef( [ x for x in zip(*annotations_internality) ] )[0][1])

    print(annotations_stability)
    print(cronbachs_alpha(annotations_stability))
    print(np.corrcoef( [ x for x in zip(*annotations_stability) ] )[0][1])

    print(annotations_globality)
    print(cronbachs_alpha(annotations_globality))
    print(np.corrcoef( [ x for x in zip(*annotations_globality) ] )[0][1])


if __name__ == "__main__":
    main()
