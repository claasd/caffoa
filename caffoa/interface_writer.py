import logging
import os
from typing import List

from caffoa.base_writer import BaseWriter
from caffoa.converter import get_response_type
from caffoa.model import EndPoint


class InterfaceWriter(BaseWriter):
    def __init__(self, version: int, name: str, namespace: str, target_folder: str):
        super().__init__(version)
        self.version = version
        self.target_folder = target_folder
        self.use_factory = False
        self.namespace = namespace
        self.imports = list()
        self.interface_name = f"I{name}Service"
        self.interface_method_template = self.load_template("InterfaceMethod.cs")
        self.interface_template = self.load_template("InterfaceTemplate.cs")
        self.factory_interface_template = self.load_template("FactoryInterfaceTemplate.cs")

    def write(self, endpoints: List[EndPoint]):
        os.makedirs(self.target_folder, exist_ok=True)

        interfaces = []
        for ep in endpoints:
            interfaces.append(self.format_endpoint(ep))

        imports = ["System.Collections.Generic"]
        imports.extend(self.imports)
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


    def format_endpoint(self, endpoint: EndPoint):

        params = [f"{param.type} {param.name}" for param in endpoint.parameters]
        if endpoint.needs_content and self.version == 1:
            params.append("HttpContent contentPayload")
        elif self.version > 1 and not self.use_factory:
            params.append("HttpRequest request")
        formatted_params = ", ".join(params)
        result = ""
        if self.version > 2:
            type = get_response_type(endpoint)
            if type is None:
                result = "<IActionResult>"
            elif type.name is None:
                result = ""
            else:
                result = f"<{type.name}>"

        return self.interface_method_template.format(NAME=endpoint.name,
                                                     PARAMS=formatted_params,
                                                     RESULT=result,
                                                     DOC="\n\t\t/// ".join(endpoint.documentation))

