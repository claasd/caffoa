import logging
from typing import List, Optional

from prance import ResolvingParser

from caffoa.converter import to_camelcase, parse_type, is_primitive
from caffoa.model import EndPoint, Parameter, Response
from caffoa.object_parser import BaseObjectParser


class PathParser:
    def __init__(self, parser: ResolvingParser):
        self.suffix = ""
        self.prefix = ""
        self.parser = parser
        self.responses = dict()
        self.bodies = dict()
        self.known_types = list()

    def create_returns(self, model_parser: ResolvingParser):
        for path, options in model_parser.specification['paths'].items():
            for operation, config in options.items():
                operation = operation.lower()
                if operation in ["parameters"]:
                    continue
                if "operationId" not in config:
                    raise Warning(f"operationId is missing for {path}: {operation}")
                operation_id = config["operationId"]
                code = None
                try:
                    responses = list()
                    for code, data in config.get("responses").items():
                        if "$ref" in data:
                            ref = data["$ref"].split('/')[-1]
                            data = model_parser.specification['components']['responses'][ref]
                        response = Response(code)
                        response.content = self.parse_content(data)
                        responses.append(response)
                    self.responses[operation_id] = responses

                except Warning as msg:
                    logging.warning(
                        f"Cannot generate typed responses for {msg} for {operation_id} ({path}): {operation}/{code}")

    def create_bodies(self, model_parser: ResolvingParser):
        for path, options in model_parser.specification['paths'].items():
            for operation, config in options.items():
                operation = operation.lower()
                if operation in ["parameters"]:
                    continue
                if "operationId" not in config:
                    raise Warning(f"operationId is missing for {path}: {operation}")
                operation_id = config["operationId"]
                if "requestBody" in config:
                    try:
                        self.bodies[operation_id] = self.parse_content(config["requestBody"])
                    except Warning as msg:
                        logging.warning(
                            f"Cannot generate typed requestBody for {msg} for {operation_id} ({path}): {operation}")

    def parse_content(self, config: dict) -> Optional[str]:

        if "content" in config:
            content = config["content"]
            keys = list(content.keys())
            if len(keys) > 1:
                raise Warning(
                    f"multiple possible responses")
            type = str(keys[0])
            if type.lower() != "application/json":
                raise Warning(
                    f"type {type}. Only application/json is currently supported for")
            try:
                schema = content[type]['schema']
            except KeyError:
                raise Warning(
                    f"type {type}. no schema found")
            if "$ref" in schema:
                return self.name_for_ref(schema["$ref"])
            if "type" in schema and is_primitive(schema["type"]):
                return parse_type(schema)
            if "type" in schema and schema["type"].lower() == "array":
                if "$ref" in schema["items"]:
                    name = self.name_for_ref(schema["items"]["$ref"])
                    return f"IEnumerable<{name}>"
                if "type" in schema["items"] and is_primitive(schema["items"]["type"]):
                    type = parse_type(schema["items"])
                    return f"IEnumerable<{type}>"
                raise Warning("array with complex type that is not a reference")

            raise Warning(
                "complex type. Only array, ref or basic types are supported.")

        return None

    def parse(self) -> List[EndPoint]:
        endpoints = list()
        for path, options in self.parser.specification['paths'].items():
            path = str(path).strip('/')
            base_parameters = list()
            if "parameters" in options:
                base_parameters = self.parse_params(options["parameters"])
            for operation, config in options.items():
                operation = operation.lower()
                if operation in ["parameters"]:
                    continue
                if "operationId" not in config:
                    raise Warning(f"OperationId is missing for {path}: {operation}")
                operation_id = config['operationId']
                operation_name = self.operation_name(operation_id)
                documentation = config['description'].split("\n")
                for response, response_data in config["responses"].items():
                    documentation.append(f"{response} -> {response_data['description']}")

                parameters = base_parameters.copy()
                if "parameters" in config:
                    parameters.extend(self.parse_params(config["parameters"]))
                needs_content = "requestBody" in config
                ep = EndPoint(operation_id, operation_name, path, operation, parameters, documentation, needs_content)
                ep.responses = self.responses.get(operation_id)
                ep.body = self.bodies.get(operation_id)
                endpoints.append(ep)
        return endpoints

    def name_for_ref(self, ref):
        name = BaseObjectParser(self.prefix, self.suffix).class_name_from_ref(ref)
        if name in self.known_types:
            return dict(self.known_types[name])["type"]
        return name

    @staticmethod
    def operation_name(operation_id) -> str:
        return to_camelcase(operation_id) + "Async"

    @staticmethod
    def parse_params(params: list) -> list:
        parameters = list()
        for param in params:
            if param['in'].lower() == "path":
                parameters.append(Parameter(param['name'], parse_type(param['schema']), param.get('description')))
        return parameters
