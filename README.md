# aiosched - Python asyncio jobs scheduler

Executes specified asyncio jobs with a chosen interval. Has relatively small
number of features but it's fast.

<img src="https://img.shields.io/pypi/v/aiosched.svg" /> <img src="https://img.shields.io/badge/license-MIT-green" /> <img src="https://img.shields.io/badge/python-3.5%20%7C%203.6%20%7C%203.7-blue.svg" />

## Why one more scheduler?

* it's extremely accurate and fast
* it's simple
* all methods are thread-safe

## Example

```python
from aiosched import scheduler
import asyncio

async def test1(a, b, c):
    print(f'JOB1 {a} {b} {c}')

async def test2():
    print('JOB2')

async def test3():
    print('JOB3')

from aiosched import scheduler

loop = asyncio.new_event_loop()
scheduler.start(loop=loop)
# jobs can be added before actual start in pending mode
job1 = scheduler.create_threadsafe(target=test1, args=(1, 2, 3), interval=1)
job2 = scheduler.create_threadsafe(target=test2, interval=0.5)
# run job once after 5 seconds
job3 = scheduler.create_threadsafe(target=test3, number=1, timer=5)
# cancel job 2
scheduler.cancel(job2)
# equal to
job2.cancel()

loop.run_forever()
```

or run scheduler loop as coroutine:

```python
loop = asyncio.new_event_loop()
job1 = scheduler.create_threadsafe(target=test1, args=(1,2,3), interval=0.1)
job2 = scheduler.create_threadsafe(target=test2, interval=0.1)
loop.run_until_complete(scheduler.scheduler_loop())
```

## Install

```shell
pip3 install aiosched
```

## Advanced

Read **AsyncJobScheduler** and **AsyncScheduledJob** classes documentation in
pydoc.
