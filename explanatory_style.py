import gate

class Event(gate.Annotation):
    def __init__(self,
                 annotation):
        super().__init__(
            annotation._annotation_element,
            annotation._annotation_file,
        )
        self._polarity = None

    @property
    def polarity(self):
        if not self._polarity:
            polarity = (
                self.features["Polarity"]
                .value
                .lower()
            )
            if "neg" in polarity.lower():
                self._polarity = -1
            elif "pos" in polarity.lower():
                self._polarity = 1
            return self._polarity
        else:
            return self._polarity

class Attribution(gate.Annotation):
    def __init__(self,
                 annotation):
        super().__init__(
            annotation._annotation_element,
            annotation._annotation_file,
        )
        self._dimensions = None

    @property
    def dimensions(self):
        if not self._dimensions:
            dimensions = {
                "Personal_v_External": None,
                "Permanent_v_Temporary": None,
                "Pervasive_v_Specific": None,
            }
            for key in dimensions.keys():
                dimensions[key] = int(
                    self.features[key]
                    .value
                    .split(" ")[0]
                )
            self._dimensions = {
                "internality" : dimensions["Personal_v_External"],
                "stability" : dimensions["Permanent_v_Temporary"],
                "globality" : dimensions["Pervasive_v_Specific"],
            }
            return self._dimensions
        else:
            return self._dimensions

    def _get_caused_event(self, events):
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
            attribution._get_caused_event(events),
            attribution
        )
        for attribution in attributions
    ]

def get_event_attribution_units_from_annotations(annotations):
    """Given an iterable of Annotation objects, return a list of
    EventAttributionUnit objects
    """
    events = [
        Event(annotation)
        for annotation in annotations
        if annotation.type.lower() == "event"
    ]
    attributions = (
        Attribution(annotation)
        for annotation in annotations
        if annotation.type.lower() == "attribution"
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
