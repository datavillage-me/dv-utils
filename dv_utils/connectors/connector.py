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

            if not value and default:
                value = default

            if value:
                setattr(config, p, value)

        return config


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
