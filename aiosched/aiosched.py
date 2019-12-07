import logging
import asyncio
import threading
import time
import uuid

MIN_INTERVAL = 0.001

logger = logging.getLogger('aiosched')


class AsyncScheduledJob:
    """
    Scheduled job object

    Automatically generated and returned by scheduler's put and put_threadsafe
    methods.
    """

    def __init__(self,
                 target,
                 args=(),
                 kwargs={},
                 interval=0,
                 timer=0,
                 number=0):
        """
        Args:
            target: coroutine function
            args: tuple with functions args
            kwargs: dict with function kwargs
            interval: interval in seconds to execute the function
            timer: job start timer
            number: how many times run job (0 = unlimited)
        """
        self.id = str(uuid.uuid4())
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self.interval = interval if interval > MIN_INTERVAL else MIN_INTERVAL
        self.number = number
        if target is None:
            self.t = 0
        else:
            self.schedule(at=timer)
        self.__active = True

    def cancel(self):
        self.__active = False
        logger.debug('job {} canceled'.format(self.id))

    @property
    def active(self):
        return self.__active

    def schedule(self, at=0):
        """
        Schedule first job execution

        Called automatically when object is created

        Args:
            at: schedule job seconds from now
        """
        self.t = time.perf_counter() + at
        logger.debug('job {} scheduled'.format(self.id))

    def reschedule(self):
        """
        Re-schedule job for the next interval
        """
        self.t += self.interval
        logger.debug('job {} re-scheduled'.format(self.id))

    def __cmp__(self, other):
        return cmp(self.t, other.t) if \
                other is not None else 1

    def __lt__(self, other):
        return (self.t < other.t) if \
                other is not None else True

    def __gt__(self, other):
        return (self.t > other.t) if \
                other is not None else True


class AsyncJobScheduler:
    """
    Job scheduler
    """

    def __init__(self, id=None):
        self.__waiting = set()
        self.__lock = threading.RLock()
        self.__stopped = threading.Event()
        self.__loop = None
        self.__sleep_coro = None
        self.id = id if id is not None else str(uuid.uuid4())

    async def scheduler_loop(self):
        """
        Scheduler loop, can be started manually as coro, or with start() method
        """
        try:
            self.__Q
        except AttributeError:
            await self._init_queue()
        try:
            logger.debug('scheduler {} started'.format(self.id))
            while True:
                job = await self.__Q.get()
                try:
                    # empty target = stop loop
                    if job.target is None: break
                    # is job cancelled?
                    if not job.active: continue
                    # no, execute
                    delta = job.t - time.perf_counter()
                    if delta > 0:
                        # create sleep coro to wait until job time is came
                        # sleep coro is canceled when new job is created or
                        # canceled
                        with self.__lock:
                            coro = asyncio.sleep(delta, loop=self.__loop)
                            self.__sleep_coro = asyncio.ensure_future(coro)
                        try:
                            await self.__sleep_coro
                        except asyncio.CancelledError:
                            pass
                        finally:
                            self.__sleep_coro = None
                        # was job canceled while we sleep?
                        if not job.active: continue
                    # no, try executing
                    # has job scheduled time come?
                    if delta <= 0 or job.t <= time.perf_counter():
                        loop = self.__loop if self.__loop else \
                                asyncio.get_event_loop()
                        # and run it
                        logger.debug(
                            'scheduler {} executing job {}, target: {}'.format(
                                self.id, job.id, job.target))
                        loop.create_task(job.target(*job.args, **job.kwargs))
                        if job.number > 0:
                            job.number -= 1
                            if job.number == 0: continue
                        job.reschedule()
                    # put job back to the queue
                    logger.debug('scheduler {} requeueing job {}'.format(
                        self.id, job.id))
                    await self.__Q.put(job)
                finally:
                    self.__Q.task_done()
        finally:
            self.__stopped.set()
            logger.debug('scheduler {} stopped'.format(self.id))

    def set_loop(self, loop=None):
        self.__loop = loop

    def start(self, loop=None):
        """
        Start scheduler

        Args:
            loop: asyncio loop
        """
        self.set_loop(loop)
        asyncio.ensure_future(self.scheduler_loop(), loop=self.__loop)

    def stop(self, wait=True):
        """
        Stop scheduler

        Args:
            wait: If True - wait until stopped, if numeric - specified number
                of seconds
        """
        try:
            asyncio.run_coroutine_threadsafe(self.__Q.put(
                AsyncScheduledJob(target=None)),
                                             loop=self.__loop)
        except AttributeError:
            raise RuntimeError('scheduler is not started')
        with self.__lock:
            try:
                self.__sleep_coro.cancel()
            except:
                pass
        if wait: self.__stopped.wait(timeout=None if wait is True else wait)

    async def _init_queue(self):
        with self.__lock:
            self.__Q = asyncio.PriorityQueue()
            for job in self.__waiting:
                await self._put_job(job)

    def create_threadsafe(self, target, **kwargs):
        """
        Create and put new job (thread-safe)

        Note: empty job target stops the scheduler

        Args:
            target: job target
            args: tuple with functions args
            kwargs: dict with function kwargs
            interval: interval in seconds to execute the function
        """
        job = AsyncScheduledJob(target, **kwargs)
        with self.__lock:
            try:
                self.__Q
                asyncio.run_coroutine_threadsafe(self._put_job(job),
                                                 loop=self.__loop)
            except AttributeError:
                self.__waiting.add(job)
        return job

    async def create(self, target, **kwargs):
        """
        Create and put new job

        Note: empty job target stops the scheduler

        Args:
            target: job target
            args: tuple with functions args
            kwargs: dict with function kwargs
            interval: interval in seconds to execute the function
        """
        job = AsyncScheduledJob(target, **kwargs)
        await self._put_job(job)
        return job

    async def _put_job(self, job):
        with self.__lock:
            logger.debug('scheduler {} new job {}'.format(self.id, job.id))
            self.__Q.put_nowait(job)
            try:
                self.__sleep_coro.cancel()
            except:
                pass

    def cancel(self, job):
        """
        Cancel scheduled job

        Equal to job.cancel()

        Args:
            job: job object
        """
        return job.cancel()
