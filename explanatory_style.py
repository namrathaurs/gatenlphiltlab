import gate


class EventAttributionUnit:
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
