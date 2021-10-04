import logging
import os
from typing import List

from caffoa import duplication_handler
from caffoa.base_writer import BaseWriter
from caffoa.converter import to_camelcase
from caffoa.model import ModelData, MemberData, ModelObjectData, ModelInterfaceData


class ModelWriter(BaseWriter):
    def __init__(self, version: int, namespace: str, output_folder: str):
        super().__init__(version)
        self.output_folder = output_folder
        self.namespace = namespace
        self.additional_imports = list()

        self.model_template = self.load_template("ModelTemplate.cs")
        self.prop_template = self.load_template("ModelPropertyTemplate.cs")
        self.interface_template = self.load_template("ModelInterfaceTemplate.cs")

    def write(self, models: List[ModelData]):
        os.makedirs(self.output_folder, exist_ok=True)
        dates_in_models = False
        for model in models:
            if duplication_handler.should_generate(model.name):
                if model.is_interface():
                    self.write_interface(model)
                else:
                    self.write_model(model)
                    if self.dates_in_model(model):
                        dates_in_models = True
                duplication_handler.store_generated(model.name)

        if dates_in_models:
            self.write_custom_date_converter()

    @staticmethod
    def dates_in_model(model: ModelData):
        for prop in model.properties:
            if prop.is_date:
                return True
        return False

    def write_model(self, model: ModelObjectData):
        imports = [f"using {key};\n" for key in model.imports]
        imports.extend([f"using {key};\n" for key in self.additional_imports])
        # remove duplicates but keep order:
        imports = list(dict.fromkeys(imports))
        all_parents = model.interfaces
        if model.parent:
            all_parents.insert(0,model.parent)
        parent = f" : {', '.join(all_parents)}" if all_parents else ""
        formatted_properties = []
        for prop in model.properties:
            formatted_properties.append(self.format_property(prop))
        formatted_updater = self.format_updater(model)

        file_name = os.path.abspath(self.output_folder + f"/{model.name}.generated.cs")
        logging.info(f"Writing class {model.name} -> {file_name}")

        description = "/// AUTOGENERED BY caffoa ///\n\t"
        if model.description is not None:
            model_description = model.description.strip().replace("\n", "\n\t/// ")
            description += f"/// <summary>\n\t/// {model_description}\n\t/// </summary>\n\t"

        with open(file_name, "w", encoding="utf-8") as f:
            f.write(self.model_template.format(NAMESPACE=self.namespace,
                                               NAME=model.name,
                                               RAWNAME=model.rawname,
                                               PROPERTIES="\n\n".join(formatted_properties),
                                               UPDATEPROPS=formatted_updater,
                                               IMPORTS="".join(imports),
                                               PARENTS=parent,
                                               DESCRIPTION=description))

    def write_interface(self, model: ModelInterfaceData):
        file_name = os.path.abspath(self.output_folder + f"/{model.name}.generated.cs")
        logging.info(f"Writing class {model.name} -> {file_name}")
        description = "/// AUTOGENERED BY caffoa ///\n\t"
        if model.description is not None:
            model_description = model.description.strip().replace("\n", "\n\t/// ")
            description += f"/// <summary>\n\t/// {model_description}\n\t/// </summary>\n\t"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(self.interface_template.format(
                NAMESPACE=self.namespace,
                NAME=model.name,
                DESCRIPTION=description,
                TYPE=model.discriminator))


    def format_property(self, property: MemberData) -> str:
        extra = ""
        if property.is_date:
            extra = "[JsonConverter(typeof(CustomJsonDateConverter))]\n\t\t"
        default_str = ""
        if property.default_value is not None:
            default_str = f" = {property.default_value};"

        json_property_extra = ""
        if property.is_required and property.nullable:
            json_property_extra = ", Required = Required.AllowNull"
        elif property.is_required:
            json_property_extra = ", Required = Required.Always"

        description = ""
        if property.description is not None:
            description = property.description.strip().replace("\n", "\n\t\t/// ")
            description = f"/// <summary>\n\t\t/// {description}\n\t\t/// </summary>\n\t\t"

        enums = ""
        if property.enums is not None:
            enums = f"{property.enums}\n\n\t\t"

        return self.prop_template.format(TYPE=property.typename,
                                         NAMELOWER=property.name,
                                         NAMEUPPER=to_camelcase(property.name),
                                         JSON_EXTRA=extra,
                                         DEFAULT=default_str,
                                         JSON_PROPERTY_EXTRA=json_property_extra,
                                         DESCRIPTION=description,
                                         ENUMS=enums)


    def format_updater(self, model: ModelData) -> str:
        props_update = []
        for prop in model.properties:
            name = to_camelcase(prop.name)
            special_call = ""
            if prop.is_list:
                if prop.is_basic_type:
                    special_call = ".ToList()"
            elif not prop.is_basic_type:
                special_call = f".To{prop.typename}()"
                if prop.nullable:
                    special_call = "?" + special_call
            props_update.append(f"{name} = other.{name}{special_call};")
        formatted = "\n\t\t\t".join(props_update)
        if model.parent:
            formatted = f"UpdateWith{model.parent}(other);\n\t\t\t{formatted}"
        return formatted


    def write_custom_date_converter(self):
        template = self.load_template("DateSerializer.cs")
        file_name = os.path.abspath(self.output_folder + f"/CustomJsonDateConverter.generated.cs")
        logging.info(f"Writing CustomJsonDateConverter -> {file_name}")
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(template.format(NAMESPACE=self.namespace))
