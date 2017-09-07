import itertools
import os
from lxml import etree as ET
import gate


conversations_path = "/home/nick/hilt/pes/conversations"

annotation_files = list(
    itertools.chain.from_iterable(
        (
            [
                os.path.join(
                    results[0],
                    x,
                )
                for x in results[2]
                if x.lower().endswith(".xml")
            ]
            for results in os.walk(conversations_path)
        )
    )
)

for f in annotation_files:
    annotation_file = gate.AnnotationFile(f)
    changes = False
    for annotation in gate.filter_annotations_by_type(
        annotation_file.iter_annotations(),
        "attribution",
        with_continuations=True,
    ):
        for feature in annotation.get_features():
            if "cause" in feature.get_name().lower():
                feature.set_name("Caused_Event")
                changes = True
    if changes:
        annotation_file.tree.write(annotation_file.filename)
        print("changes written: " + f)
    else:
        print("no changes made: " + f)
