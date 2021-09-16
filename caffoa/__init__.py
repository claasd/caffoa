import argparse
import yaml

import caffoa.duplication_handler
from caffoa.function import generate_functions
from caffoa.openapi_file import OpenApiFile


def execute2():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="caffoa.yml", help="Path to config file (Default: caffoa.yml)")
    args = parser.parse_args()
    with open(args.config, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not "services" in data:
        raise Warning("no services in config file.")
    services = data["services"]
    if type(services) != list:
        raise Warning("services should be list")
    try:
        settings = data["config"]
        if type(settings) != dict:
            raise Warning("config should be key/values pairs")
    except KeyError:
        settings = dict()
    duplication_handler.init(settings.get("duplicates", "overwrite"))
    version = settings.get("version", 1)
    for number, config in enumerate(services):
        if not "apiPath" in config:
            raise Warning(f"apiPath is required for service #{number}")
        handler = OpenApiFile(config["apiPath"], version)
        if "model" in config:
            handler.create_model(config["model"])

        if "function" in config:
            function = config["function"]
            if not "name" in function or not "namespace" in function or not "targetFolder" in function:
                raise Warning(f"function needs children 'name', 'namespace' and 'targetFolder' in service #{id}")
            name = function['name']
            namespace = function["namespace"]
            target_folder = function['targetFolder']
            boilerplate = function.get('boilerplate')
            interface_name = function.get('interfaceName', f"I{name}Service")
            functions_name = function.get('functionsName', f"{name}Functions")
            interface_namespace = function.get('interfaceNamespace', namespace)
            interface_target_folder = function.get('interfaceTargetFolder', target_folder)
            imports = function.get('imports', list())
            generate_functions(config["apiPath"], target_folder, functions_name, namespace, interface_target_folder,
                               interface_name, interface_namespace, boilerplate, imports, version)
