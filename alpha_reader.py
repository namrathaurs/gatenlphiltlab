from collections import namedtuple
from itertools import groupby
import csv
import numpy as np
import pandas
import skll
import explanatory_style as es


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

if __name__ == "__main__":

    with open("/home/nick/hilt/pes/csvs/eaus.csv") as eaus_file:
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

    annotations = {}
    for dimension_name in es.EventAttributionUnit.dimensions:
        annotations.update(
            {
                dimension_name + "Pos" :
                itemize_from_df_grouping(
                    df_positives_by_eaus,
                    dimension_name
                ),
                dimension_name + "Neg" :
                itemize_from_df_grouping(
                    df_negatives_by_eaus,
                    dimension_name
                ),
                dimension_name + "PosNeg" :
                itemize_from_df_grouping(
                    df_by_eaus,
                    dimension_name
                ),
            }
        )
    annotations.update(
        {
            "CoPos" :
            itemize_from_df_grouping(
                df_positives_by_eaus,
                "composite",
            ),
            "CoNeg" :
            itemize_from_df_grouping(
                df_negatives_by_eaus,
                "composite",
            ),
            "CoPosNeg" :
            itemize_from_df_grouping(
                df_negatives_by_eaus,
                "composite",
            ),
        }
    )

    IRRStat = namedtuple("IRRStat", ["kappa", "pearsons", "cronbachs"])
    irr_stats = {}
    for key, annotation_items in annotations.items():
        kappa = skll.kappa(
            [ x[0] for x in annotation_items ],
            [ x[1] for x in annotation_items ],
            weights="linear"
        )
        pearsons = np.corrcoef(
            [ x for x in zip(*annotation_items) ]
        )[0,1]
        cronbachs = cronbachs_alpha(annotation_items)
        irr_stats.update(
            {
                key :
                IRRStat(
                    kappa=kappa,
                    pearsons=pearsons,
                    cronbachs=cronbachs,
                )
            }
        )

    scores_df = (
        pandas.DataFrame(
            data=irr_stats,
            index=IRRStat._fields,
        )
        .transpose()
    )
    print(scores_df)
    with open("/home/nick/hilt/pes/csvs/dimension_scores.csv", "w") as scores_file:
        scores_df.to_csv(scores_file)
