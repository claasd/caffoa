import logging
from typing import List, Optional

from prance import ResolvingParser

from caffoa.content_parser import ContentParser
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
        self.known_types = dict()

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
        one_of_schemas = dict()
        for name, schema in model_parser.specification['components']["schemas"].items():
            if "oneOf" in schema:
                one_of_schemas[name] = schema

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
                        self.bodies[operation_id] = ContentParser(self.known_types, self.prefix,
                                                                  self.suffix).parse_content_list(config["requestBody"],
                                                                                                  one_of_schemas)
                    except Warning as msg:
                        logging.warning(
                            f"Cannot generate typed requestBody for {msg} for {operation_id} ({path}): {operation}")

    def parse_content(self, config: dict) -> Optional[str]:
        return ContentParser(self.known_types, self.prefix, self.suffix).parse_content_string(config)

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
