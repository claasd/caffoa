import logging
import os
from typing import List

from caffoa.model import EndPoint


class InterfaceWriter:
    def __init__(self, version: int, name: str, namespace: str, target_folder: str):
        self.version = version
        self.target_folder = target_folder
        self.namespace = namespace
        self.interface_name = f"I{name}Service"
        self.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"data/v{version}")
        with open(self.template_folder + "/InterfaceMethod.cs", "r", encoding="utf-8") as f:
            self.interface_method_template = f.read()
        with open(self.template_folder + "/InterfaceTemplate.cs", "r", encoding="utf-8") as f:
            self.interface_template = f.read()

    def write(self, endpoints: List[EndPoint]):
        os.makedirs(self.target_folder, exist_ok=True)
        interfaces = []
        for ep in endpoints:
            interfaces.append(self.format_endpoint(ep))

        file_name = os.path.abspath(f"{self.target_folder}/{self.interface_name}.generated.cs")
        logging.info(f"Writing Interface to {file_name}")
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(self.interface_template.format(METHODS="\n\n".join(interfaces),
                                                   NAMESPACE=self.namespace,
                                                   IMPORTS="",
                                                   CLASSNAME=self.interface_name))

    def format_endpoint(self, endpoint: EndPoint):

        params = [f"{param.type} {param.name}" for param in endpoint.parameters]
        if endpoint.needs_content and self.version == 1:
            params.append("HttpContent contentPayload")
        elif self.version == 2:
            params.append("HttpRequest request")
        formatted_params = ", ".join(params)
        return self.interface_method_template.format(NAME=endpoint.name,
                                                     PARAMS=formatted_params,
                                                     DOC="\n\t\t/// ".join(endpoint.documentation))
