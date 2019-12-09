__version__ = '0.0.24'

from .aiosched import AsyncJobScheduler, AsyncScheduledJob, _data

# default scheduler
scheduler = AsyncJobScheduler('default')

def set_debug(mode=True):
    _data.debug = mode
