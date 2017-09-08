from itertools import groupby
import csv
import numpy as np
import pandas
import skll


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
    return alpha

def itemize_from_df(dataframe,
                    item_name):
    return tuple(
        x for x in dataframe[item_name]
    )

def itemize_from_df_grouping(grouping,
                             item_name):
    """
    dataframe -> pandas.DataFrame object
    item_name -> str; column name
    grouping_keys -> [str]; column names
    """
    raw_items = [
        itemize_from_df(group, item_name)
        for _, group in grouping
    ]
    len_fully_annotated = max( len(x) for x in raw_items )
    return [
        item for item in raw_items
        if len(item) == len_fully_annotated
    ]

def group_by_eau(dataframe):
    return dataframe.groupby(
        [
            "attr_id",
            "attr_start_node",
            "attr_end_node",
        ]
    )

with open("/home/nick/test/gate/expl/eaus.csv") as eaus_file:
    df = pandas.read_csv( eaus_file, dtype={"attr_id":str} )
df["composite"] = sum(
    df[x] for x in [
        "internality",
        "stability",
        "globality"
    ]
)

df_by_eaus = group_by_eau(df)

df_by_positives = df.groupby("polarity").get_group(1)
df_by_negatives = df.groupby("polarity").get_group(0)

df_positives_by_eaus = group_by_eau(df_by_positives)
df_negatives_by_eaus = group_by_eau(df_by_negatives)

# print(
#     itemize_from_df_grouping(group_by_eau(df_by_negatives),"internality")
# )

annotations = {
    "internalityPos" : itemize_from_df_grouping(
        df_positives_by_eaus,
        "internality"
    ),
    "stabilityPos" : itemize_from_df_grouping(
        df_positives_by_eaus,
        "stability"
    ),
    "globalityPos" : itemize_from_df_grouping(
        df_positives_by_eaus,
        "globality"
    ),

    "internalityNeg" : itemize_from_df_grouping(
        df_negatives_by_eaus,
        "internality"
    ),
    "stabilityNeg" : itemize_from_df_grouping(
        df_negatives_by_eaus,
        "stability"
    ),
    "globalityNeg" : itemize_from_df_grouping(
        df_negatives_by_eaus,
        "globality"
    ),

    "internalityPosNeg" : itemize_from_df_grouping(
        df_by_eaus,
        "internality"
    ),
    "stabilityPosNeg" : itemize_from_df_grouping(
        df_by_eaus,
        "stability"
    ),
    "globalityPosNeg" : itemize_from_df_grouping(
        df_by_eaus,
        "globality"
    ),
}

print(
    skll.kappa(
        [x[0] for x in annotations["internalityPosNeg"]],
        [x[1] for x in annotations["internalityPosNeg"]],
        weights="linear"
    )
)
quit()
###

irr_stats = {
    "internalityPos",
    "stabilityPos",
    "globalityPos",

    "internalityNeg",
    "stabilityNeg",
    "globalityNeg",

    "internalityPosNeg",
    "stabilityPosNeg",
    "globalityPosNeg",

    "CoPosNeg",
    "CoPos",
    "CoNeg",

    "CPCN",
}


###

internality_kappa = skll.kappa(
    [x[0] for x in internality_annotations],
    [x[1] for x in internality_annotations],
    weights="linear"
)
stability_kappa = skll.kappa(
    [x[0] for x in stability_annotations],
    [x[1] for x in stability_annotations],
    weights="linear"
)
globality_kappa = skll.kappa(
    [x[0] for x in globality_annotations],
    [x[1] for x in globality_annotations],
    weights="linear"
)

internality_pearsons = np.corrcoef([x for x in zip(*internality_annotations)])[0,1]
stability_pearsons = np.corrcoef([x for x in zip(*stability_annotations)])[0,1]
globality_pearsons = np.corrcoef([x for x in zip(*globality_annotations)])[0,1]

print("internality:")
print("alpha = " + str(cronbachs_alpha(internality_annotations)))
print("linear kappa = " + str(internality_kappa))
print("pearson's corrcoef = " + str(internality_pearsons))
print()

print("stability:")
print("alpha = " + str(cronbachs_alpha(stability_annotations)))
print("linear kappa = " + str(stability_kappa))
print("pearson's corrcoef = " + str(stability_pearsons))
print()

print("globality:")
print("alpha = " + str(cronbachs_alpha(globality_annotations)))
print("linear kappa = " + str(globality_kappa))
print("pearson's corrcoef = " + str(globality_pearsons))
print()

