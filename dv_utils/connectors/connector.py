import json
import logging
import importlib.resources as importlib_resources

logger = logging.getLogger(__name__)


class Configuration():
    schema_file: str = None

    def __str__(self):
        return str([(var, getattr(self, var)) for var in vars(self)])


def populate_configuration(connector_id, config: Configuration, config_dir='/resources/data') -> Configuration:
    filename = f'{config_dir}/configuration_{connector_id}.json'

    schema = None
    with importlib_resources.open_text('dv_utils.connectors', config.schema_file) as config_file:
        schema = json.load(config_file)['schema']

    with open(filename, 'r') as file:
        data = json.load(file)
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
