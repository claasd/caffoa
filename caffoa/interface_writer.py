import logging
import os
from typing import List

from caffoa.base_writer import BaseWriter
from caffoa.body_type_filter import BodyTypeFilter
from caffoa.converter import get_response_type
from caffoa.model import EndPoint


class InterfaceWriter(BaseWriter):
    def __init__(self, version: int, name: str, namespace: str, target_folder: str):
        super().__init__(version)
        self.version = version
        self.target_folder = target_folder
        self.use_factory = True if version >= 3 else False
        self.namespace = namespace
        self.imports = list()
        self.request_body_filter = list()
        self.interface_name = f"I{name}Service"
        self.interface_method_template = self.load_template("InterfaceMethod.cs")
        self.interface_template = self.load_template("InterfaceTemplate.cs")
        self.factory_interface_template = self.load_template("FactoryInterfaceTemplate.cs")

    def write(self, endpoints: List[EndPoint]):
        os.makedirs(self.target_folder, exist_ok=True)

        interfaces = []
        imports = ["System.Collections.Generic"]
        for ep in endpoints:
            interfaces.extend(self.format_endpoints(ep))
            imports.extend(BodyTypeFilter(self.request_body_filter).additional_imports(ep))
        imports.extend(self.imports)
        # remove duplicates but keep order:
        imports = list(dict.fromkeys(imports))
        imports_str = "".join([f"using {imp};\n" for imp in imports])

        file_name = os.path.abspath(f"{self.target_folder}/{self.interface_name}.generated.cs")
        logging.info(f"Writing Interface to {file_name}")
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(self.interface_template.format(METHODS="\n\n".join(interfaces),
                                                   NAMESPACE=self.namespace,
                                                   IMPORTS=imports_str,
                                                   CLASSNAME=self.interface_name))
        if self.version > 1 and self.use_factory:
            file_name = os.path.abspath(f"{self.target_folder}/{self.interface_name}Factory.generated.cs")
            logging.info(f"Writing Factory Interface to {file_name}")
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(self.factory_interface_template.format(NAMESPACE=self.namespace,
                                                               CLASSNAME=self.interface_name))

    def format_endpoints(self, endpoint: EndPoint) -> List[str]:
        base_params = [f"{param.type} {param.name}" for param in endpoint.parameters]
        if self.version == 1:
            params = base_params.copy()
            if endpoint.needs_content:
                params.append("HttpContent contentPayload")
            return [self.format_endpoint(endpoint, params, "")]

        type = get_response_type(endpoint)
        if type is None:
            result = "<IActionResult>"
        elif type.name is None:
            result = ""
        else:
            result = f"<{type.name}>"
        params = base_params.copy()
        filtered_body = BodyTypeFilter(self.request_body_filter).body_type(endpoint)
        if filtered_body:
            params.append(f"{filtered_body} payload")
            if not self.use_factory:
                params.append("HttpRequest request")
            return [self.format_endpoint(endpoint, params, result)]
        if not endpoint.body:
            if endpoint.needs_content and self.use_factory:
                params.append(f"Stream stream")
            if not self.use_factory:
                params.append("HttpRequest request")
            return [self.format_endpoint(endpoint, params, result)]
        interfaces = list()
        for body in endpoint.body.types:
            params = base_params.copy()
            params.append(f"{body} payload")
            if not self.use_factory:
                params.append("HttpRequest request")
            interfaces.append(self.format_endpoint(endpoint, params, result))
        return interfaces

    def format_endpoint(self, endpoint: EndPoint, params: list, result: str):
        formatted_params = ", ".join(params)
        return self.interface_method_template.format(NAME=endpoint.name,
                                                     PARAMS=formatted_params,
                                                     RESULT=result,
                                                     DOC="\n\t\t/// ".join(endpoint.documentation))
