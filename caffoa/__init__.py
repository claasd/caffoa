import argparse
from caffoa.function import generate_functions
from caffoa.schema import generate_schemas


def execute():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["functions", "schemas"])
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-folder", required=True)
    parser.add_argument("--class-name", required=False)
    parser.add_argument("--namespace", required=True)
    args = parser.parse_args()
    if args.command == "functions":
        generate_functions(args.input, args.output_folder, args.class_name, args.namespace)
    elif args.command == "schemas":
        generate_schemas(args.input, args.output_folder, args.namespace)
