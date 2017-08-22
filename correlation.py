import numpy as np

def average(values):
    return sum(values) / len(list(values))

def squared_difference(value, average):
    return ( value - average )**2

def variance(values):
    try:
        return average(
            [
                squared_difference(
                    value,
                    average(values)
                )
                for value in values
            ]
        )
    except ZeroDivisionError:
        return 0

def cronbachs_alpha(annotations):

    num_items = len(annotations)
    sum_component_variances = sum(
        variance(item) for item in annotations
    )
    overall_variance = variance( list( sum( annotations, () ) ) )

    alpha = (
        ( num_items / (num_items - 1) )
        * ( 1 - sum_component_variances / overall_variance )
    )

    return (
        num_items,
        sum_component_variances,
        round(overall_variance,2),
        round(alpha,2)
    )
    return alpha
# def cronbachs_alpha(annotations):

#     num_items = len(annotations)
#     sum_component_variances = sum(
#         np.var(item) for item in annotations
#     )
#     overall_variance = np.var(annotations)
#     # overall_variance = np.var(
#     #     [
#     #         sum(person)
#     #         for person in zip(*annotations)
#     #     ]
#     # )

#     alpha = (
#         ( num_items / (num_items - 1) )
#         * ( 1 - sum_component_variances / overall_variance )
#     )

#     return alpha

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

    annotations = list(
        zip(
            *[
                sorted(
                    (
                        x for x in gate.AnnotationGroup(
                            _ for _ in annotation_file.iter_annotations()
                        ).get_annotations()
                        if (x._type == "Attribution")
                    ),
                    key=lambda x: x._id
                )
                for annotation_file in annotation_files
            ]
        )
    )

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

    print("internality:")
    print(annotations_internality)
    print(cronbachs_alpha(annotations_internality))
    print()

    print("stability:")
    print(annotations_stability)
    print(cronbachs_alpha(annotations_stability))
    print()

    print("globality:")
    print(annotations_globality)
    print(cronbachs_alpha(annotations_globality))
    print()


if __name__ == "__main__":
    main()
