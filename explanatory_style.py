import gate


class EventAttributionUnit:
    def __init__(self, event, attribution):
        """event, attribution must be gate.Annotation objects
        """
        self._event = event
        self._attribution = attribution
        for annotation in [self._event, self._attribution]:
            if not isinstance(annotation, gate.Annotation):
                raise TypeError("Not a gate.Annotation object!")

        self._polarity = (
            gate.get_feature_by_name("Polarity", self._event)
            .get_value()
            .lower()
        )

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

# def CoPos():
# def CoNeg():

if __name__ == "__main__":

    test_file = "/home/nick/hilt/pes/conversations/16/4-MG-2014-06-02_PES_3_consensus.xml"


    annotation_file = gate.AnnotationFile(test_file)
    text_with_nodes = annotation_file._text_with_nodes

    raw_events = []
    raw_attributions = []
    annotations = annotation_file.iter_annotations()
    for annotation in annotations:
        if "event" in annotation._type.lower():
            raw_events.append(annotation)
        elif "attribution" in annotation._type.lower():
            raw_attributions.append(annotation)

    events = gate.concatenate_annotations(raw_events)
    attributions = gate.concatenate_annotations(raw_attributions)

    event_attribution_units = get_event_attribution_units(
        events,
        attributions
    )

    for x in event_attribution_units:
        print(
            x._polarity,
        )
