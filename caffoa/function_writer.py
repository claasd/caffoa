import logging
import os
from typing import List

from caffoa.model import EndPoint


class FunctionWriter:
    def __init__(self, version: int, name: str, namespace: str, target_folder: str, interface_name: str):
        self.interface_name = interface_name
        self.version = version
        self.target_folder = target_folder
        self.namespace = namespace
        self.boilerplate = "{BASE}"
        self.functions_name = f"{name}Functions"
        self.imports = list()
        self.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"data/v{version}")
        with open(self.template_folder + "/FunctionMethod.cs", "r", encoding="utf-8") as f:
            self.method_template = f.read()
        with open(self.template_folder + "/FunctionTemplate.cs", "r", encoding="utf-8") as f:
            self.class_template = f.read()

    def write(self, endpoints: List[EndPoint]):
        os.makedirs(self.target_folder, exist_ok=True)
        function_endpoints = []
        for ep in endpoints:
            function_endpoints.append(self.format_endpoint(ep))

        imports = [f"using {x};\n" for x in self.imports]
        file_name = os.path.abspath(f"{self.target_folder}/{self.functions_name}.generated.cs")
        logging.info(f"Writing Functions to {file_name}")
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(self.class_template.format(METHODS="\n\n".join(function_endpoints),
                                               NAMESPACE=self.namespace,
                                               CLASSNAME=self.functions_name,
                                               INTERFACENAME=self.interface_name,
                                               IMPORTS="".join(imports)))

    def format_endpoint(self, endpoint: EndPoint) -> str:
        param_names = [param.name for param in endpoint.parameters]
        if endpoint.needs_content and self.version == 1:
            param_names.append("req.Content")
        elif self.version == 2:
            param_names.append("request")
        formatted_param_names = ", ".join(param_names)

        function_call = f"{endpoint.name}({formatted_param_names})"
        if self.version == 1:
            default_call = f"return await Service(req, log).{function_call};"
        else:
            default_call = f"return await _service.{function_call};"

        params_with_names = [f"{param.type} {param.name}" for param in endpoint.parameters]
        formatted_params_with_names = ", " + ", ".join(params_with_names) if len(params_with_names) > 0 else ""
        extra_error_info = [f'debugInformation["p_{param.name}"] = {param.name}.ToString();\n\t\t\t\t' for param in
                            endpoint.parameters]

        invocation = self.boilerplate.replace("{BASE}", default_call) \
            .replace("{CALL}", function_call) \
            .replace("\n", "\n\t\t\t\t").strip()
        return self.method_template.format(NAME=endpoint.name,
                                           OPERATION=endpoint.operation,
                                           PATH=endpoint.path,
                                           INVOCATION=invocation,
                                           PARAMS=formatted_params_with_names,
                                           PARAM_NAMES=formatted_param_names,
                                           ADDITIONAL_ERROR_INFOS="".join(extra_error_info))
