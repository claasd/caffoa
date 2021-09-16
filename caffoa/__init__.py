import argparse
import yaml

from caffoa.duplication_handler import DuplicationHandler
from caffoa.function import generate_functions
from caffoa.schema import generate_schemas


def execute():
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
    duplication_handler = DuplicationHandler(settings.get("duplicates", "overwrite"))
    version = settings.get("version", 1)
    for id, config in enumerate(services):
        if not "apiPath" in config:
            raise Warning(f"apiPath is required for service #{id}")
        api = config["apiPath"]
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
            generate_functions(api, target_folder, functions_name, namespace, interface_target_folder, interface_name,
                               interface_namespace, boilerplate, imports, version)

        if "model" in config:
            model = config["model"]
            prefix = model.get("prefix", "")
            suffix = model.get("suffix", "")
            imports = model.get("imports", list())
            if not "namespace" in model or not "targetFolder" in model:
                raise Warning(f"model needs children 'namespace' and 'targetFolder' in service #{id}")
            excludes = list(model.get('excludes', list()))
            includes = list(model.get('includes', list()))
            generate_schemas(api, model["targetFolder"], model['namespace'], prefix, suffix, excludes, includes, duplication_handler, version, imports)
