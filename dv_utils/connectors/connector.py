import json
import re
import os
import requests
import logging
import importlib.resources as importlib_resources

from ..settings import Settings
from ..settings import settings as default_settings

logger = logging.getLogger(__name__)

class Configuration():
    schema_file: str = None
    connector_id: str = None

    def __str__(self):
        return str([(var, getattr(self, var)) for var in vars(self)])


def populate_configuration(connector_id, config: Configuration, config_dir='/resources/data') -> Configuration:
    
    config.connector_id=connector_id

    filename = f'{config_dir}/configuration_{connector_id}.json'

    #check if file is available on http end point or stored on mounted dick
    try:
        if filename.startswith("http"):
            data=requests.get(filename).json()
        else:
            with open(filename, 'r') as file:
                data = json.load(file)
    
        schema = None
        with importlib_resources.open_text('dv_utils.connectors', config.schema_file) as config_file:
            schema = json.load(config_file)['schema']
        
        #replace environment variables
        __substitude_env_vars(data)

        keys = data['connectorKeys']

        for p in schema:
            schema_field = schema[p]
            value = keys.get(p)

            default = schema_field.get('default', "")
            type = schema_field.get('type', "string")

            if not value and default:
                value = default

            value = __parse_value(value, type)

            if value:
                setattr(config, p, value)

        return config
    except Exception as inst:
        logger.error(f"Not able to open connector configuration file: {inst}")
        raise
        

def __parse_value(value: str, type: str):
    type_cleaned = type.strip().lower()
    if(type_cleaned in ['string', 'str']):
        return value

    if(type_cleaned in ['bool', 'boolean']):
        return __parse_boolean_value(value)

def __parse_boolean_value(value: str):
    value_cleaned = value.strip().lower()
    
    if(value_cleaned in ['true', '1']):
        return True
    
    elif(value_cleaned in ['false', '0']):
        return False
    
    logger.warn(f"Value {value} not a valid boolean value. Using `false`")
    return False

def __substitude_env_vars(d):
    for key in d.keys():
        v = d.get(key)
        if isinstance(v, str):
            m = re.match('\${(\w+)}', v)
            if m:
                env_name = m.group(1)
                env_val =default_settings.config(env_name)
                if env_val is None:
                    env_val = ""
                d[key] = env_val
        elif isinstance(v, dict):
            __substitude_env_vars(v)

def is_valid_configuration(config: Configuration):
    schema = None
    with importlib_resources.open_text('dv_utils.connectors', config.schema_file) as config_file:
        schema = json.load(config_file)['schema']

    for p in schema:
        schema_field = schema[p]
        value = getattr(config, p)

        is_required = bool(schema_field.get('required'))

        if not value and is_required:
            logger.error(f"Missing configured field <{p}>")
            return False

    return True
