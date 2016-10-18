# importance-kappa

This is a Python 3 program meant to be run with arguments in the command line.

usage: importance-kappa [-h] [--csv-header] [--csv-output] [--annotation-set ANNOTATION_SET] annotation_type source1 source2

calculates Cohen's Kappa scores from CompanionBot Importance annotations

positional arguments:
	annotation_type
		the annotation type to gather
	source1
		the first source annotation file
	source2
		the second source annotation file

optional arguments:
	-h, --help
		show this help message and exit

	--csv-header
		print the header line for stats in CSV format to terminal: (file1,file2,total,agreement,chance,kappa_score)

	--csv-output
		print stats in CSV format to terminal: (file1,file2,total,agreement,chance,kappa_score)

	--annotation-set ANNOTATION_SET
		specifies the annotation set from which to gather annotations
