import asyncio
import sys
import uvloop
from functools import wraps

def do_n_times(n=2):
    # this returns a function that _actually_ gets passed the wrapped method.
    def wrapper(func):
        @wraps(func)
        async def wrapper_do_n_times():
            for _ in range(n-1):
                await func()
            return await func()
        return wrapper_do_n_times
    return wrapper

@do_n_times(n=4)
async def print_me():
    print("me")
    pass

if sys.version_info >= (3, 11):
    with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
        runner.run(print_me())
else:
    uvloop.install()
    asyncio.run(print_me())
