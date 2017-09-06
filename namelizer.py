import itertools
import os
from lxml import etree as ET
import gate


conversations_path = "/home/nick/hilt/pes/conversations"

files = list(
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

annotation_files = (
    gate.AnnotationFile(f)
    for f in files
)

for f in annotation_files:
    for annotation in f.iter_annotations():
        if annotation._type.lower() == "event":
            for feature in annotation.get_features():
                if "positive" in feature.get_name().lower():
                    feature.set_name("Polarity")
                    f.tree.write(f.filename)

# print(
#     set(
#         feature.get_name()
#         for annotation_file in annotation_files
#         for annotation in annotation_file.iter_annotations()
#         for feature in annotation.get_features()
#         if annotation._type.lower() == "event"
#     )
# )
