import logging
from typing import List

from prance import ResolvingParser

from caffoa.converter import to_camelcase, parse_type
from caffoa.model import EndPoint, Parameter, Response
from caffoa.object_parser import BaseObjectParser


class PathParser:
    def __init__(self, parser: ResolvingParser):
        self.suffix = ""
        self.prefix = ""
        self.parser = parser
        self.responses = dict()

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
                        responses.append(self.parse_response(code, data))
                    self.responses[operation_id] = responses

                except Warning as msg:
                    logging.warning(f"{msg} for {operation_id} ({path}): {operation}/{code}")

    def parse_response(self, code: str, config: dict) -> Response:
        response = Response(code)
        if "content" in config:
            content = config["content"]
            keys = list(content.keys())
            if len(keys) > 1:
                raise Warning(
                    f"Cannot generate typed responses for multiple possible responses")
            type = str(keys[0])
            if type.lower() != "application/json":
                raise Warning(
                    f"Cannot generate typed responses for for type {type}. Only application/json is currently supported for")
            schema = content[type]['schema']
            object_parser = BaseObjectParser(self.prefix, self.suffix)
            if "$ref" in schema:
                response.content = object_parser.class_name_from_ref(schema["$ref"])
            elif "type" in schema and schema["type"].lower() == "array":
                if "$ref" not in schema["items"]:
                    raise Warning("Cannot create response type for array without reference")
                name = object_parser.class_name_from_ref(schema["items"]["$ref"])
                response.content = f"IEnumerable<{name}>"
            else:
                raise Warning("Cannot generate typed responses: only responses with direct reference or array with reference are supported")

        return response

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
                ep = EndPoint(operation_name, path, operation, parameters, documentation, needs_content)
                ep.responses = self.responses.get(operation_id)
                endpoints.append(ep)
                print(ep)
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
