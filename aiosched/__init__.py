__version__ = '0.0.17'

from .aiosched import AsyncJobScheduler, AsyncScheduledJob

# default scheduler
scheduler = AsyncJobScheduler('default')
