from prance import ResolvingParser
from prance.util.resolver import RESOLVE_HTTP, RESOLVE_FILES, TRANSLATE_EXTERNAL

from caffoa.model_parser import ModelParser
from caffoa.model_writer import ModelWriter


class OpenApiFile:
    def __init__(self, name: str, version: int):
        self.version = version
        self.name = name
        self._model_parser = None

    def model_parser(self):
        if self._model_parser is None:
            self._model_parser = ResolvingParser(self.name, strict=False, resolve_types=RESOLVE_HTTP | RESOLVE_FILES,
                                                 resolve_method=TRANSLATE_EXTERNAL)
            schemas = self._model_parser.specification["components"]["schemas"]
            for class_name in list(schemas.keys()):
                if ".yml_schemas_" in class_name:
                    new_class_name = class_name.split(".yml_schemas_")[-1]
                    schemas[new_class_name] = schemas[class_name]
                    del schemas[class_name]

        return self._model_parser

    def create_model(self, config: dict):
        if not "namespace" in config or not "targetFolder" in config:
            raise Warning(f"model needs children 'namespace' and 'targetFolder' in service #{id}")
        parser = ModelParser()
        parser.prefix = config.get("prefix", "")
        parser.suffix = config.get("suffix", "")

        parser.excludes = list(config.get('excludes', list()))
        parser.includes = list(config.get('includes', list()))
        model = parser.parse(self.model_parser())
        writer = ModelWriter(self.version, config["namespace"], config["targetFolder"])
        writer.additional_imports = config.get("imports", list())
        writer.write(model)
