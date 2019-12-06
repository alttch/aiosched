# aiosched - Python asyncio jobs scheduler

Executes specified asyncio jobs with a chosen interval. Has relatively small
number of features but it's fast.

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
# tsks can be added before actual start in pending mode
job1 = scheduler.create_threadsafe(target=test1, args=(1,2,3), interval=0.1)
job2 = scheduler.create_threadsafe(target=test2, interval=2)
job3 = scheduler.create_threadsafe(target=test3, interval=0.5)
# cancel job 2
scheduler.cancel(job2)
loop.run_forever()
```

or run as scheduler loop directly as coroutine:

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
