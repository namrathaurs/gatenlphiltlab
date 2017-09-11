import gate


class EventAttributionUnit:

    polarities = {
        "negative" : 0,
        "positive" : 1,
    }

    dimensions = {
        name : [ x+1 for x in range(7) ] for name in [
            "internality",
            "stability",
            "globality",
        ]
    }

    def __init__(self,
                 event,
                 attribution):
        """event, attribution must be gate.Annotation objects
        """
        self._event = event
        self._attribution = attribution
        for annotation in [self._event, self._attribution]:
            if not isinstance(annotation, gate.Annotation):
                raise TypeError("Not a gate.Annotation object!")

        polarity = (
            gate.get_feature_by_name("Polarity", self._event)
            .get_value()
            .lower()
        )

        if "neg" in polarity:
            self._polarity = 0
        elif "pos" in polarity:
            self._polarity = 1

        # extract dimensions from annotations using 3 P's terminology
        dimensions = {
            "pers": None,
            "perm": None,
            "perv": None,
        }
        for key in dimensions.keys():
            dimensions[key] = int(
                gate.get_feature_by_name(key, self._attribution)
                .get_value()
                .split(" ")[0]
            )

        self._internality = dimensions["pers"]
        self._stability = dimensions["perm"]
        self._globality = dimensions["perv"]

        self._dimensions = {
            "internality" : self._internality,
            "stability" : self._stability,
            "globality" : self._globality,
        }

    def get_event(self):
        return self._event

    def get_attribution(self):
        return self._attribution

    def get_polarity(self):
        return self._polarity

    def get_internality(self):
        return self._internality

    def get_stability(self):
        return self._stability

    def get_globality(self):
        return self._globality

    def get_dimensions(self):
        return self._dimensions

def get_event_attribution_units(events,
                                attributions):
    """Given an iterable of events and one of attributions, return a list of
    EventAttributionUnit objects
    """
    return [
        EventAttributionUnit(
            attribution.get_caused_event(events),
            attribution
        )
        for attribution in attributions
    ]

def get_event_attribution_units_from_annotations(annotation_iterable,
                                                 with_continuations=False):
    """Given an iterable of Annotation objects, return a list of
    EventAttributionUnit objects
    """
    annotations = gate.concatenate_annotations(
        gate.filter_annotations_by_type(
            annotation_iterable,
            "event",
            "attribution",
            with_continuations=with_continuations,
        )
    )
    events = gate.filter_annotations_by_type(
        annotations,
        "event",
        with_continuations=with_continuations,
    )
    attributions = gate.filter_annotations_by_type(
        annotations,
        "attribution",
        with_continuations=with_continuations,
    )
    return get_event_attribution_units(
        events,
        attributions,
    )

if __name__ == "__main__":

    import csv
    import argparse

    parser = argparse.ArgumentParser(
        description="Extracts information about EAUs contained within given "
        "GATE files and writes to a CSV file"
    )
    parser.add_argument(
        "-c",
        "--with-continuations",
        dest="with_continuations",
        action="store_true",
        default=False,
        help="include annotation continuations"
    )
    parser.add_argument(
        "-o",
        "--output-file",
        dest="output_file",
        required="true",
        help="destination file"
    )
    parser.add_argument(
        "-i",
        "--annotation-files",
        dest="annotation_files",
        nargs="+",
        required="true",
        help="GATE annotation files"
    )
    args = parser.parse_args()

    with open(args.output_file, "w") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=[
                "attr_id",
                "attr_start_node",
                "attr_end_node",
                "polarity",
                "internality",
                "stability",
                "globality",
            ]
        )
        writer.writeheader()

        for f in args.annotation_files:
            annotation_file = gate.AnnotationFile(f)
            annotations = annotation_file.iter_annotations()

            EAUs = get_event_attribution_units_from_annotations(
                annotations,
                with_continuations=args.with_continuations
            )
            for EAU in EAUs:
                writer.writerow(
                    {
                        "attr_id" : EAU.get_attribution()._id,
                        "attr_start_node" : EAU.get_attribution()._start_node,
                        "attr_end_node" : EAU.get_attribution()._end_node,
                        "polarity" : EAU.get_polarity(),
                        "internality" : EAU.get_internality(),
                        "stability" : EAU.get_stability(),
                        "globality" : EAU.get_globality(),
                    }
                )
