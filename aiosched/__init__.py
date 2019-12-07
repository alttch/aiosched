__version__ = '0.0.14'

from .aiosched import AsyncJobScheduler, AsyncScheduledJob

# default scheduler
scheduler = AsyncJobScheduler('default')
