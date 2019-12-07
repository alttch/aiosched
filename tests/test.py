#!/usr/bin/env python3

from pathlib import Path
import sys
import asyncio
import threading
import time
import unittest
import logging

from types import SimpleNamespace

sys.path.insert(0, Path(__file__).absolute().parents[1].as_posix())

result = SimpleNamespace(test001a=0, test001b=0, test002a=0, test002b=10)

from aiosched import scheduler, AsyncJobScheduler, AsyncScheduledJob


class Test(unittest.TestCase):

    def test001_periodic(self):

        async def test1():
            result.test001a += 1

        async def test2():
            result.test001b += 1

        j1 = scheduler.create_threadsafe(target=test1, interval=0.01)
        j2 = scheduler.create_threadsafe(target=test2, interval=0.01)

        time.sleep(0.1)

        j2.cancel()

        r1 = result.test001a
        r2 = result.test001b

        self.assertGreater(r1, 9)
        self.assertGreater(r2, 9)

        time.sleep(0.1)

        self.assertLess(r1, result.test001a)
        self.assertEqual(r2, result.test001b)

    def test002_periodic_and_number(self):

        async def test1():
            result.test002a += 1

        async def test2():
            result.test002b -= 1

        j1 = scheduler.create_threadsafe(target=test1, interval=0.01, timer=0.2)
        j2 = scheduler.create_threadsafe(target=test2,
                                         interval=0.01,
                                         number=10,
                                         timer=0.2)

        time.sleep(0.1)
        self.assertEqual(result.test002a, 0)
        self.assertEqual(result.test002b, 10)

        time.sleep(0.2)
        self.assertEqual(result.test002b, 0)
        self.assertGreater(result.test001a, 20)


def _t_start():
    loop = asyncio.new_event_loop()
    scheduler.set_loop(loop)
    loop.run_until_complete(scheduler.scheduler_loop())


if __name__ == '__main__':
    threading.Thread(target=_t_start).start()
    try:
        test_suite = unittest.TestLoader().loadTestsFromTestCase(Test)
        test_result = unittest.TextTestRunner().run(test_suite)
        sys.exit(not test_result.wasSuccessful())
    finally:
        time.sleep(0.1)
        scheduler.stop()
