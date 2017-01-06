#!/usr/bin/env python3

print('test')
import argparse

parser = argparse.ArgumentParser(
    description='''automatically supplies baseline annotations to'''
    ''' Importance annotation files.'''
    )
parser.add_argument(
    'input-file',
    dest='input_file',
    type=argparse.FileType(mode='w', encoding='UTF-8'),
    nargs='+',
    )

input_files = parser.parse_args().input_file
