from typing import Any

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

    def get_config(self, config: dict, name: str, default_value: Any = None):
        return config.get(name, self.base_config.get(name, default_value))

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
                pass  # no schema

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
        writer.additional_imports.extend(config.get("imports", self.base_config.get('imports', list())))
        writer.enum_name = self.get_config(config, "enumName", writer.enum_name)
        writer.enum_list_name = self.get_config(config, "enumListName", writer.enum_list_name)
        writer.check_enums = self.get_config(config, "checkEnums", writer.check_enums)

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
            parser.create_bodies(self.model_parser())
        return parser.parse()

    def create_function(self, config: dict):
        if not "name" in config or not "namespace" in config or not "targetFolder" in config:
            raise Warning(f"function needs children 'name', 'namespace' and 'targetFolder' in service {self.name}")

        endpoints = self.parse_endpoints(self.version > 2)

        name = config['name']
        namespace = config["namespace"]
        target_folder = config['targetFolder']

        iwriter = InterfaceWriter(self.version, name, namespace, target_folder)
        iwriter.use_factory = self.get_config(config, "useFactory", iwriter.use_factory)

        iwriter.imports.extend(self.get_config(config, "imports", list()))
        iwriter.imports.extend(self.imports)
        iwriter.interface_name = self.get_config(config, 'interfaceName', iwriter.interface_name)
        iwriter.namespace = self.get_config(config, 'interfaceNamespace', iwriter.namespace)
        iwriter.target_folder = self.get_config(config, 'interfaceTargetFolder', iwriter.target_folder)
        iwriter.request_body_filter = self.get_config(config, 'requestBodyType', iwriter.request_body_filter)
        iwriter.write(endpoints)

        writer = FunctionWriter(self.version, name, namespace, target_folder, iwriter.interface_name)
        writer.use_factory = self.get_config(config, 'useFactory', writer.use_factory)
        writer.boilerplate = self.get_config(config, 'boilerplate', writer.boilerplate)
        writer.functions_name = self.get_config(config, 'functionsName', writer.functions_name)
        writer.error_namespace = self.get_config(config, "errorNamespace", writer.error_namespace)
        writer.json_error_handling = self.get_config(config, "jsonErrorHandling", writer.json_error_handling)
        writer.error_folder = self.get_config(config, "errorFolder", writer.error_folder)
        writer.imports.extend(self.get_config(config, "imports", list()))
        writer.request_body_filter = self.get_config(config, 'requestBodyType', list())
        if self.version > 2:
            writer.imports.extend(self.imports)
        writer.write(endpoints)
