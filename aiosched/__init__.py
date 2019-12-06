__version__ = '0.0.6'

from .aiosched import AsyncJobScheduler, AsyncScheduledJob

# default scheduler
scheduler = AsyncJobScheduler()
