import gate
import explanatory_style as es


test_file = "/home/nick/test/gate/expl/4-MG-2014-06-02_PES_3_NB.xml"


annotation_file = gate.AnnotationFile(test_file)
text_with_nodes = annotation_file._text_with_nodes

events = gate.concatenate_annotations(
    annotation
    for annotation in annotation_file.iter_annotations()
    if annotation._type.lower().startswith("event")
)
attributions = gate.concatenate_annotations(
    annotation
    for annotation in annotation_file.iter_annotations()
    if annotation._type.lower().startswith("attribution")
)

event_attribution_units = (
    es.get_event_attribution_units(events,
                                   attributions)
)

for x in event_attribution_units:
    print(x.get_attribution().get_concatenated_text(text_with_nodes, " "))
quit()

for attribution in attributions:
    for event in events:
        if event._id == attribution._caused_event_id:
            print(
                explanatory_style.EventAttributionUnit(event, attribution)
            )
