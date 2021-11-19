import argparse
import glob
import logging
import os

import yaml

from caffoa import duplication_handler
from caffoa.openapi_file import OpenApiFile


def execute():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="caffoa.yml", help="Path to config file (Default: caffoa.yml)")
    args = parser.parse_args()
    with open(args.config, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not "services" in data:
        raise Warning("no services in config file.")
    services = data["services"]
    if type(services) != list:
        raise Warning("services should be list")
    try:
        settings = data["config"]
        if type(settings) != dict:
            raise Warning("config should be key/values pairs")
    except KeyError:
        settings = dict()
    version = settings.get("version", 1)
    duplication_handler.init(settings.get("duplicates", "overwrite"))

    if settings.get('clearGeneratedFiles', False):
        old_files = glob.glob('**/*.generated.cs', recursive=True)
        for file in old_files:
            logging.info(f"Removing {file}")
            os.unlink(file)


    for number, config in enumerate(services):
        if not "apiPath" in config:
            raise Warning(f"apiPath is required for service #{number}")
        api_config = settings.copy()
        api_config.update(config.get("config", dict()))
        handler = OpenApiFile(config["apiPath"], version, api_config)
        if "model" in config:
            handler.create_model(config["model"])

        if "function" in config:
            handler.create_function(config["function"])
