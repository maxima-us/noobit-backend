"""
A bare-bones wrapper class that allows us to turn off heartbeating if we don't want it.
"""
import subprocess
from server import settings
from . import locate

class Heartbeat(object):
    def __init__(self, heartbeat_key: str, is_active=False):
        self.is_active = is_active
        dir_path = locate.heartbeat_dir()
        
        # dir_path = f"{settings.ROOT}/monitor"
        
        self.filename = f'{dir_path}/{heartbeat_key}.txt'

    # def heartbeat(self, heartbeat_key):
    #     if self.is_active is True:
    #         filename = '%s.txt' % heartbeat_key
    #         subprocess.call(['touch', filename])

    def beat(self):
        if self.is_active is True:
            subprocess.call(['touch', self.filename])
