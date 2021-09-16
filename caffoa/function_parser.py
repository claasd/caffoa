from typing import List

from prance import ResolvingParser

from caffoa.converter import to_camelcase, parse_type
from caffoa.function import parse_params
from caffoa.model import EndPoint, Parameter


class FunctionParser:
    def __init__(self, parser: ResolvingParser):
        self.parser = parser

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
                operation_id = to_camelcase(config['operationId']) + "Async"
                documentation = config['description'].split("\n")
                for response, response_data in config["responses"].items():
                    documentation.append(f"{response} -> {response_data['description']}")
                parameters = base_parameters.copy()
                if "parameters" in config:
                    parameters.extend(parse_params(config["parameters"]))
                needs_content = "requestBody" in config
                endpoints.append(EndPoint(operation_id, path, operation, parameters, documentation, needs_content))
        return endpoints

    @staticmethod
    def parse_params(params: list) -> list:
        parameters = list()
        for param in params:
            if param['in'].lower() == "path":
                parameters.append(Parameter(param['name'], parse_type(param['schema']), param.get('description')))
        return parameters
