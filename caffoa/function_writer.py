import logging
import os
from typing import List

from caffoa.base_writer import BaseWriter
from caffoa.converter import get_response_type
from caffoa.model import EndPoint


class FunctionWriter(BaseWriter):
    def __init__(self, version: int, name: str, namespace: str, target_folder: str, interface_name: str):
        super().__init__(version)
        self.interface_name = interface_name
        self.version = version
        self.target_folder = target_folder
        self.namespace = namespace
        self.boilerplate = "{BASE}"
        self.functions_name = f"{name}Functions"
        self.imports = list()
        self.method_template = self.load_template("FunctionMethod.cs")
        self.class_template = self.load_template("FunctionTemplate.cs")
        self.caffoa_error_template = self.load_template("CaffoaClientError.cs")
        self.client_error_template = self.load_template("ClientErrorTemplate.cs")
        self.generic_client_error_template = self.load_template("GenericClientErrorTemplate.cs")

    def write(self, endpoints: List[EndPoint]):
        os.makedirs(self.target_folder, exist_ok=True)
        imports = []
        imports.extend(self.imports)
        if self.version > 2:
            self.write_errors(endpoints)
            imports.append(self.namespace + ".Errors")
        function_endpoints = []
        for ep in endpoints:
            function_endpoints.append(self.format_endpoint(ep))

        imports = [f"using {x};\n" for x in imports]
        file_name = os.path.abspath(f"{self.target_folder}/{self.functions_name}.generated.cs")
        logging.info(f"Writing Functions to {file_name}")
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(self.class_template.format(METHODS="\n\n".join(function_endpoints),
                                               NAMESPACE=self.namespace,
                                               CLASSNAME=self.functions_name,
                                               INTERFACENAME=self.interface_name,
                                               IMPORTS="".join(imports)))

    def format_endpoint(self, endpoint: EndPoint) -> str:
        if self.version == 1:
            template_params = self.v1_params(endpoint)
        if self.version == 2:
            template_params = self.v2_params(endpoint)
        if self.version == 3:
            template_params = self.v3_params(endpoint)
        template_params["PARAMS"] = ", ".join(template_params["PARAMS"])
        if len(template_params["PARAM_NAMES"]) > 0:
            template_params["PARAM_NAMES"] = ", " + (", ".join(template_params["PARAM_NAMES"]))
        else:
            template_params["PARAM_NAMES"] = ""
        return self.method_template.format_map(template_params)

    def v1_params(self, endpoint: EndPoint) -> dict:
        template_params = self.default_params(endpoint)
        if endpoint.needs_content:
            template_params['PARAMS'].append("req.Content")
        params = ", ".join(template_params["PARAMS"])
        function_call = f"{endpoint.name}({params})"
        default_call = f"return await Service(req, log).{function_call};"
        template_params["INVOCATION"] = self.boilerplate.replace("{BASE}", default_call) \
            .replace("{CALL}", function_call) \
            .replace("\n", "\n\t\t\t\t").strip()
        return template_params

    def v2_params(self, endpoint: EndPoint) -> dict:
        template_params = self.default_params(endpoint)
        template_params['PARAMS'].append("request")
        params = ", ".join(template_params["PARAMS"])
        function_call = f"{endpoint.name}({params})"
        default_call = f"return await _service.{function_call};"
        template_params["INVOCATION"] = self.boilerplate.replace("{BASE}", default_call) \
            .replace("{CALL}", function_call) \
            .replace("\n", "\n\t\t\t\t").strip()
        return template_params

    def v3_params(self, endpoint: EndPoint) -> dict:
        params = self.default_params(endpoint)
        params['PARAMS'].append("request")
        type = get_response_type(endpoint)
        params['VALUE'] = "var result = "
        if type is None:
            params['RESULT'] = "result"
        elif type.name is None and type.is_simple:
            params['RESULT'] = f"new StatusCodeResult({type.code})"
            params['VALUE'] = ""
        elif type.name is None:
            params['RESULT'] = f"new StatusCodeResult(result)"
        elif type.is_simple:
            params['RESULT'] = f"new JsonResult(result) {{StatusCode = {type.code}}}"
        elif type.base is None:
            params['RESULT'] = "new StatusCodeResult((int)result.ResultCode)"
        else:
            params['RESULT'] = "new JsonResult(result.Data) {StatusCode = (int)result.ResultCode}"
        return params

    @staticmethod
    def default_params(endpoint: EndPoint) -> dict:
        extra_error_info = [f'debugInformation["p_{param.name}"] = {param.name}.ToString();\n\t\t\t\t' for param in
                            endpoint.parameters]
        return dict(
            NAME=endpoint.name,
            OPERATION=endpoint.operation,
            PATH=endpoint.path,
            PARAMS=[param.name for param in endpoint.parameters],
            PARAM_NAMES=[f"{param.type} {param.name}" for param in endpoint.parameters],
            ADDITIONAL_ERROR_INFOS="".join(extra_error_info),
            INVOCATION="",
            RESULT="",
            VALUE=""
        )

    def write_errors(self, endpoints: List[EndPoint]):
        error_classes = dict()
        generic_error_classes = dict()
        for endpoint in endpoints:
            if endpoint.responses is None:
                continue
            for response in endpoint.responses:
                if 400 <= response.code < 500:
                    name = response.content
                    if name is None:
                        generic_error_classes[f'Generic{response.code}'] = response.code
                        continue
                    if name in error_classes:
                        if error_classes[name] != response.code:
                            raise Warning(
                                "The same response object with different error codes is currently not supported")
                    error_classes[name] = response.code

        imports_str = "".join([f"using {imp};\n" for imp in self.imports])
        os.makedirs(self.target_folder + "/Errors", exist_ok=True)
        file_name = os.path.abspath(f"{self.target_folder}/Errors/CaffoaClientError.generated.cs")
        logging.info(f"Writing Client Error to {file_name}")
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(self.caffoa_error_template.format(NAMESPACE=self.namespace + ".Errors"))

        for name, code in error_classes.items():
            file_name = os.path.abspath(f"{self.target_folder}/Errors/{name}ClientError.generated.cs")
            logging.info(f"Writing Client Error to {file_name}")
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(self.client_error_template.format(NAMESPACE=self.namespace + ".Errors",
                                                          NAME=name,
                                                          CODE=code,
                                                          IMPORTS=imports_str))
        for name, code in generic_error_classes.items():
            file_name = os.path.abspath(f"{self.target_folder}/Errors/{name}ClientError.generated.cs")
            logging.info(f"Writing Client Error to {file_name}")
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(self.generic_client_error_template.format(NAMESPACE=self.namespace + ".Errors",
                                                          NAME=name,
                                                          CODE=code))