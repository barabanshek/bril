import argparse
import json
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--json-filename', dest='json_filename')

args = parser.parse_args()

json_file = open(args.json_filename)
json_data = json.load(json_file)

print ("number of functions= ", len(json_data['functions']))

json_file.close()
