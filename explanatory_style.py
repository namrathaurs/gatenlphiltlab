import gate


class EventAttributionUnit:
    """event, attribution must be gate.Annotation objects
    """
    def __init__(self, event, attribution):
        self._event = event
        self._attribution = attribution
        for annotation in [self._event, self._attribution]:
            # if type(anntotation) != "Annotation":
            if not isinstance(annotation, gate.Annotation):
                raise TypeError("Not a gate.Annotation object!")

    def get_event(self):
        return self._event

    def get_attribution(self):
        return self._attribution

def get_event_attribution_units(events, attributions):
    return [
        EventAttributionUnit( event, attribution )
        for attribution in attributions
        for event in events
        if event._id == attribution._caused_event_id
    ]

# def CoPos():
# def CoNeg():
