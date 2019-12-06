__version__ = '0.0.2'

from .aiosched import AsyncJobScheduler, AsyncScheduledJob

# default scheduler
scheduler = AsyncJobScheduler()
