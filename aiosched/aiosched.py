import asyncio
import threading
import time
import uuid


class AsyncScheduledJob:
    """
    Scheduled job object

    Automatically generated and returned by scheduler's put and put_threadsafe
    methods.
    """

    def __init__(self, target, args=(), kwargs={}, interval=0):
        """
        Args:
            target: coroutine function
            args: tuple with functions args
            kwargs: dict with function kwargs
            interval: interval in seconds to execute the function
        """
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self.interval = interval
        if target is None:
            self.t = 0
        else:
            self.schedule()
        self.id = str(uuid.uuid4())

    def schedule(self):
        """
        Schedule job execution for "right now"

        Called automatically when object is created
        """
        self.t = time.perf_counter()

    def reschedule(self):
        """
        Re-schedule job for the next interval
        """
        self.t += self.interval

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

    def __init__(self):
        self.__waiting = set()
        self.__cancelled = set()
        self.__lock = threading.RLock()
        self.__stopped = threading.Event()
        self.__loop = None
        self.__sleep_coro = None

    async def scheduler_loop(self):
        """
        Scheduler loop, can be started manually as coro, or with start() method
        """
        try:
            self.__Q
        except:
            await self._init_queue()
        try:
            while True:
                job = await self.__Q.get()
                # empty target = stop loop
                if job.target is None:
                    self.__Q.task_done()
                    break
                # is job cancelled?
                with self.__lock:
                    if job.id in self.__cancelled:
                        self.__cancelled.remove(job.id)
                        continue
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
                    with self.__lock:
                        if job.id in self.__cancelled:
                            # yes, cancel it
                            self.__cancelled.remove(job.id)
                            continue
                # no, try executing
                # has job scheduled time come?
                if delta <= 0 or job.t <= time.perf_counter():
                    # yes - reschedule
                    job.reschedule()
                    loop = self.__loop if self.__loop else \
                            asyncio.get_event_loop()
                    # and run it
                    loop.create_task(job.target(*job.args, **job.kwargs))
                # put job back to the queue
                await self.__Q.put(job)
                self.__Q.task_done()
        finally:
            self.__stopped.set()

    def start(self, loop=None):
        """
        Start scheduler

        Args:
            loop: asyncio loop
        """
        if loop: self.__loop = loop
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
        if wait: self.__stopped.wait(timeout=None if wait is True else wait)

    def cancel_all(self):
        """
        Cancel all jobs in queue
        """
        asyncio.run_coroutine_threadsafe(self._init_queue(), loop=self.__loop)

    async def _init_queue(self):
        self.__Q = asyncio.PriorityQueue()
        with self.__lock:
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
        try:
            asyncio.run_coroutine_threadsafe(self._put_job(job),
                                             loop=self.__loop)
        except AttributeError:
            with self.__lock:
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
            self.__Q.put_nowait(job)
            try:
                self.__sleep_coro.cancel()
            except:
                pass

    def cancel(self, job):
        """
        Cancel scheduled job

        Args:
            job: job object or job id
        """
        with self.__lock:
            if isinstance(job, str):
                self.__cancelled.add(job)
            else:
                self.__cancelled.add(job.id)
            try:
                self.__sleep_coro.cancel()
            except:
                pass
