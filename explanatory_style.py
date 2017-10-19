import gate

class Event(gate.Annotation):
    def __init__(self,
                 annotation):
        super().__init__(annotation._annotation_element)
        self._polarity = None

    @property
    def polarity(self):
        if not self._polarity:
            polarity = (
                gate.get_feature_by_name("polarity", self)
                .value
                .lower()
            )
            if "neg" in polarity:
                self._polarity = 0
            elif "pos" in polarity:
                self._polarity = 1
            return self._polarity
        else:
            return self._polarity

class Attribution(gate.Annotation):
    def __init__(self,
                 annotation):
        super().__init__(annotation._annotation_element)
        self._dimensions = None

    @property
    def dimensions(self):
        if not self._dimensions:
            dimensions = {
                "pers": None,
                "perm": None,
                "perv": None,
            }
            for key in dimensions.keys():
                dimensions[key] = int(
                    gate.get_feature_by_name(key, self)
                    .value
                    .split(" ")[0]
                )
            self._dimensions = {
                "internality" : dimensions["pers"],
                "stability" : dimensions["perm"],
                "globality" : dimensions["perv"],
            }
            return self._dimensions
        else:
            return self._dimensions

    def get_caused_event(self, events):
        return next(
            ( x for x in events if x.id == self._caused_event_id ),
            None
        )

class EventAttributionUnit:
    def __init__(self,
                 event,
                 attribution):
        """event, attribution must be gate.Annotation objects
        """
        self._event = event
        self._attribution = attribution
        for annotation in [self.event, self.attribution]:
            if not isinstance(annotation, gate.Annotation):
                raise TypeError("Not a gate.Annotation object!")

    @property
    def event(self):
        return self._event

    @property
    def attribution(self):
        return self._attribution

def get_event_attribution_units(events,
                                attributions):
    """Given an iterable of Events and one of Attributions, return a list of
    EventAttributionUnits
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
            [
                "event",
                "attribution",
            ],
            with_continuations=with_continuations,
        )
    )
    events = (
        Event(x)
        for x in gate.filter_annotations_by_type(
            annotations,
            ["event"],
            with_continuations=with_continuations,
        )
    )
    attributions = (
        Attribution(x)
        for x in gate.filter_annotations_by_type(
            annotations,
            ["attribution"],
            with_continuations=with_continuations,
        )
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
                        "attr_id" : EAU.attribution.id,
                        "attr_start_node" : EAU.attribution.start_node,
                        "attr_end_node" : EAU.attribution.end_node,
                        "polarity" : EAU.event.polarity,
                        "internality" : EAU.attribution.dimensions["internality"],
                        "stability" : EAU.attribution.dimensions["stability"],
                        "globality" : EAU.attribution.dimensions["globality"],
                    }
                )
