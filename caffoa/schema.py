import logging
import os

from caffoa import DuplicationHandler
from caffoa.converter import to_camelcase
from caffoa.schema_parser import SchemaParser, ModelData


def write_model(model: ModelData, output_path: str, namespace: str, version: int, imports : list):
    template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"data/v{version}")
    with open(template_folder + "/ModelTemplate.cs", "r", encoding="utf-8") as f:
        model_template = f.read()
    with open(template_folder + "/ModelPropertyTemplate.cs", "r", encoding="utf-8") as f:
        prop_Template = f.read()
    properties = list()
    imports = [f"using {key};\n" for key in imports]
    imports = "".join(model.imports) + "".join(imports)
    if len(model.parents) > 0:
        parents = " : " + ", ".join(model.parents)
    else:
        parents = ""
    has_dates = False
    for property in model.properties:
        if property.is_date:
            extra = "[JsonConverter(typeof(CustomJsonDateConverter))]\n\t\t"
            has_dates = True
        else:
            extra = ""
        default_str = ""
        if property.default_value != None:
            default_str = f" = {property.default_value};"
        json_property_extra = ""
        if property.is_required and property.nullable:
            json_property_extra = ", Required = Required.AllowNull"
        elif property.is_required:
            json_property_extra = ", Required = Required.Always"
        #        elif not property.nullable:
        #            json_property_extra = ", Required = Required.DisallowNull"

        description = ""
        if property.description != None:
            prop_description = property.description.strip().replace("\n", "\n\t\t/// ")
            description = f"/// <summary>\n\t\t/// {prop_description}\n\t\t/// </summary>\n\t\t"

        enums = ""
        if property.enums != None:
            enums = f"{property.enums}\n\n\t\t"

        properties.append(
            prop_Template.format(TYPE=property.typename, NAMELOWER=property.name, NAMEUPPER=to_camelcase(property.name),
                                 JSON_EXTRA=extra, DEFAULT=default_str, JSON_PROPERTY_EXTRA=json_property_extra,
                                 DESCRIPTION=description, ENUMS=enums))
    updateprops = []
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
        updateprops.append(f"{name} = other.{name}{special_call};")
    base_updateprops = ""
    for parent in model.parents:
        base_updateprops += f"UpdateWith{parent}(other);\n\t\t\t"
    file_name = os.path.abspath(output_path + f"/{model.name}.generated.cs")
    logging.info(f"Writing class {model.name} -> {file_name}")
    description = "/// AUTOGENERED BY caffoa ///\n\t"
    if model.description != None:
        mod_description = model.description.strip().replace("\n", "\n\t/// ")
        description += f"/// <summary>\n\t/// {mod_description}\n\t/// </summary>\n\t"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(model_template.format(NAMESPACE=namespace, NAME=model.name, RAWNAME=model.rawname,
                                      PROPERTIES="\n\n".join(properties),
                                      UPDATEPROPS="\n\t\t\t".join(updateprops), BASE_UPDATEPROPS=base_updateprops,
                                      IMPORTS=imports, PARENTS=parents, DESCRIPTION=description))
    if has_dates:
        with open(template_folder + "/DateSerializer.cs", "r", encoding="utf-8") as f:
            date_converter_template = f.read()

        file_name = os.path.abspath(output_path + f"/CustomJsonDateConverter.generated.cs")
        logging.info(f"Writing CustomJsonDateConverter -> {file_name}")
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(date_converter_template.format(NAMESPACE=namespace))


def generate_schemas(input_file: str, output_path: str, namespace: str, prefix: str, suffix: str, excludes: list,
                     includes: list, duplication_handler: DuplicationHandler, version: int, imports : list):
    parser = SchemaParser(prefix, suffix, excludes, includes)
    models = parser.parse(input_file)
    os.makedirs(output_path, exist_ok=True)
    for model in models:
        if duplication_handler.should_generate(model.name):
            write_model(model, output_path, namespace, version, imports)
            duplication_handler.store_generated(model.name)
