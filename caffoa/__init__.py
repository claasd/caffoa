import argparse
import yaml

from caffoa.function import generate_functions
from caffoa.schema import generate_schemas


def execute():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="caffea.yml", help="Path to config file (Default: caffea.yml)")
    args = parser.parse_args()
    with open(args.config, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not "services" in data:
        raise Warning("no services in config file.")
    services = data["services"]
    if type(services) != list:
        raise Warning("services should be list")
    for id, config in enumerate(services):
        if not "apiPath" in config:
            raise Warning(f"apiPath is required for service #{id}")
        api = config["apiPath"]
        if "function" in config:
            function = config["function"]
            if not "name" in function or not "namespace" in function or not "targetFolder" in function:
                raise Warning(f"function needs children 'name', 'namespace' and 'targetFolder' in service #{id}")
            generate_functions(api,function['targetFolder'], function['name'], function["namespace"])

        if "model" in config:
            model = config["model"]
            if  not "namespace" in model or not "targetFolder" in model:
                raise Warning(f"model needs children 'namespace' and 'targetFolder' in service #{id}")

            generate_schemas(api, model["targetFolder"], model['namespace'])

