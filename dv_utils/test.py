from connectors.file import FileConnector, FileConfiguration
from connectors.connector import populate_configuration

print('start')

config = populate_configuration("arne", FileConfiguration(), ".")

c = FileConnector(config)

print('done')
