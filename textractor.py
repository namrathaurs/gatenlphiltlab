from os.path import *
import argparse
import gate


class InputError(Exception):
    pass

parser = argparse.ArgumentParser(
    # TODO: update desc
    description="Writes the plain text used within "
    "a GATE document to a file"
)
parser.add_argument(
    "-i",
    "--input-file",
    dest="input_file",
    required="true",
    help="GATE annotation file"
)
parser.add_argument(
    "-o",
    "--output-file",
    dest="output_file",
    help="destination file for text output. "
    "Default is '<filename>.textraction'."
)

args = parser.parse_args()
annotation_file = gate.AnnotationFile(args.input_file)
text = annotation_file.get_text()

if args.output_file: output_file = abspath(args.output_file)
else: output_file = (
    splitext(
        abspath(args.input_file)
    )[0] + ".textraction"
)

if isfile(output_file):
    while True:
        response = input(
            "Overwrite file '{}'? y/N --> ".format(output_file)
        ).lower()
        if response == "y":
            break
        elif (response == "n") or (response == ""):
            print("Skipping file '{}'".format(output_file))
            quit()
        else: print("Error: '{}' not recognized.".format(response))

with open(output_file, "w") as destination:
    destination.write(text)

print("File written: '{}'".format(output_file))
