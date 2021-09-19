from prance import ResolvingParser
from prance.util.resolver import RESOLVE_HTTP, RESOLVE_FILES, TRANSLATE_EXTERNAL

from caffoa.function_writer import FunctionWriter
from caffoa.interface_writer import InterfaceWriter
from caffoa.model_parser import ModelParser
from caffoa.model_writer import ModelWriter
from caffoa.path_parser import PathParser


class OpenApiFile:
    def __init__(self, name: str, version: int, config: dict):
        self.version = version
        self.name = name
        self.base_config = config
        self._model_parser = None
        self._function_parser = None
        self.model = None
        self.imports = list()
        self.known_types = dict()

    def model_parser(self):
        if self._model_parser is None:
            self._model_parser = ResolvingParser(self.name, strict=False, resolve_types=RESOLVE_HTTP | RESOLVE_FILES,
                                                 resolve_method=TRANSLATE_EXTERNAL)
            try:
                schemas = self._model_parser.specification["components"]["schemas"]
                for class_name in list(schemas.keys()):
                    if ".yml_schemas_" in class_name:
                        new_class_name = class_name.split(".yml_schemas_")[-1]
                        schemas[new_class_name] = schemas[class_name]
                        del schemas[class_name]
            except KeyError:
                pass # no schema


        return self._model_parser

    def function_parser(self) -> ResolvingParser:
        if self._function_parser is None:
            self._function_parser = ResolvingParser(self.name, strict=False)
        return self._function_parser

    def create_model(self, config: dict):
        if not "namespace" in config or not "targetFolder" in config:
            raise Warning(f"model needs children 'namespace' and 'targetFolder' in service #{id}")
        parser = ModelParser()
        parser.prefix = config.get("prefix", self.base_config.get("prefix", ""))
        parser.suffix = config.get("suffix", self.base_config.get("suffix", ""))

        parser.excludes = list(config.get('excludes', list()))
        parser.includes = list(config.get('includes', list()))
        model = parser.parse(self.model_parser())
        writer = ModelWriter(self.version, config["namespace"], config["targetFolder"])
        writer.additional_imports = config.get("imports", list())
        writer.write(model)
        self.imports.append(writer.namespace)
        self.known_types = parser.known_types

    def parse_endpoints(self, create_returns: bool):
        parser = PathParser(self.function_parser())
        parser.known_types = self.known_types
        parser.prefix = self.base_config.get("prefix", "")
        parser.suffix = self.base_config.get("suffix", "")
        if create_returns:
            parser.create_returns(self.model_parser())
        return parser.parse()

    def create_function(self, config: dict):
        if not "name" in config or not "namespace" in config or not "targetFolder" in config:
            raise Warning(f"function needs children 'name', 'namespace' and 'targetFolder' in service {self.name}")

        endpoints = self.parse_endpoints(self.version > 2)

        name = config['name']
        namespace = config["namespace"]
        target_folder = config['targetFolder']

        iwriter = InterfaceWriter(self.version, name, namespace, target_folder)
        iwriter.imports.extend(config.get('imports', list()))
        iwriter.imports.extend(self.imports)
        iwriter.interface_name = config.get('interfaceName', iwriter.interface_name)
        iwriter.namespace = config.get('interfaceNamespace', iwriter.namespace)
        iwriter.target_folder = config.get('interfaceTargetFolder', iwriter.target_folder)
        iwriter.write(endpoints)

        writer = FunctionWriter(self.version, name, namespace, target_folder, iwriter.interface_name)
        writer.boilerplate = config.get('boilerplate', writer.boilerplate)
        writer.functions_name = config.get('functionsName', writer.functions_name)
        writer.error_namespace = config.get('errorNamespace', writer.error_namespace)
        writer.error_folder = config.get('errorFolder', writer.error_folder)
        writer.imports.extend(config.get('imports', list()))
        if self.version > 2:
            writer.imports.extend(self.imports)
        writer.write(endpoints)
