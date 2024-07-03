import logging
import asyncio
from cbpi.api import *
from cbpi.api.base import CBPiBase
from cbpi.api import Property, parameters
from cbpi.api.config import ConfigType
from asyncowfs.bus import Bus  # Assuming the asyncowfs library provides a Bus class
from asyncowfs.server import Server  # Assuming the asyncowfs library provides a Server class

# Initialize logger
logger = logging.getLogger(__name__)

class ArduinoOWFSConfig(CBPiExtension):

    owfs_bus = None
    owfs_server = None

    def __init__(self, cbpi):
        self.cbpi = cbpi
        self._task = asyncio.create_task(self.init_config())

    async def init_config(self):
        logger.info("Initializing Arduino OWFS Configuration")
        # Add or update configuration settings
        await self.add_or_update_config("owfs_path", "/mnt/1wire", "OWFS Mount Path", type=ConfigType.STRING)
        await self.add_or_update_config("owfs_logging_level", "INFO", "OWFS Logging Level", [
            {"label": "INFO", "value": "INFO"},
            {"label": "DEBUG", "value": "DEBUG"},
            {"label": "ERROR", "value": "ERROR"}
        ], type=ConfigType.STRING)
        
        # Set logging level based on configuration
        log_level = self.cbpi.config.get("owfs_logging_level", "INFO")
        logger.info(f"Setting log level to: {log_level}")
        if log_level == "DEBUG":
            logger.setLevel(logging.DEBUG)
        elif log_level == "ERROR":
            logger.setLevel(logging.ERROR)
        else:
            logger.setLevel(logging.INFO)
        
        # Initialize OWFS and server objects
        await self.init_owfs()

    async def init_owfs(self):
        owfs_path = self.cbpi.config.get("owfs_path", "/mnt/1wire")
        logger.info(f"Initializing OWFS Bus at path: {owfs_path}")
        try:
            self.owfs_bus = Bus(owfs_path)  # Initialize the OWFS bus object
            self.owfs_server = Server(self.owfs_bus)  # Initialize the OWFS server object
            ArduinoOWFSConfig.owfs_bus = self.owfs_bus
            ArduinoOWFSConfig.owfs_server = self.owfs_server
            logger.info("OWFS Bus and Server initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing OWFS Bus or Server: {e}")

    async def add_or_update_config(self, key, default, description, options=[], type=ConfigType.STRING):
        try:
            current_value = self.cbpi.config.get(key, None)
            if current_value is None:
                logger.debug(f"Adding new config: {key}")
                await self.cbpi.config.add(key, default, type=type, description=description, options=options)
            else:
                logger.debug(f"Updating existing config: {key}")
                await self.cbpi.config.add(key, current_value, type=type, description=description, options=options)
        except Exception as e:
            logger.warning(f'Unable to add or update config {key}: {e}')


@parameters([])
class ArduinoOWFSTemps(CBPiSensor):

    def __init__(self, cbpi, id, props):
        super(ArduinoOWFSTemps, self).__init__(cbpi, id, props)
        self.value = 0
        self.owfs_bus = ArduinoOWFSConfig.owfs_bus
        self.owfs_server = ArduinoOWFSConfig.owfs_server

    @action(key="Test", parameters=[])
    async def action1(self, **kwargs):
        print("ACTION!", kwargs)

    async def run(self):
        while self.running is True:
            self.value = (self.value + 1) % 100  # Slowly changing value between 0 and 99
            self.push_update(self.value)
            await asyncio.sleep(1)
    
    def get_state(self):
        return dict(value=self.value)


def setup(cbpi):
    cbpi.plugin.register("ArduinoOWFSConfig", ArduinoOWFSConfig)
    cbpi.plugin.register("ArduinoOWFSTemps", ArduinoOWFSTemps)
