import functools
import signal
import sys

from fastapi.responses import JSONResponse
from starlette import status
from rich import print

# max_execution_time in seconds
TILE_TIMEOUT = None

def set_tile_timeout(timeout: int):
    global TILE_TIMEOUT
    TILE_TIMEOUT = timeout

class TimeOutException(Exception):
    """It took longer than expected"""


def abort_after():
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def handle_timeout(signum, frame):
                raise TimeOutException(f"Function execution took longer than {TILE_TIMEOUT}s and was terminated")
            if sys.platform == 'win32':
                print("Won't be stopped in windows!")
            else:
                signal.signal(signal.SIGALRM, handle_timeout)
                signal.alarm(TILE_TIMEOUT)
            result = func(*args, **kwargs)
            if sys.platform != 'win32':
                signal.alarm(0)
            return result
        return wrapper
    return decorator


def timeout_response() -> JSONResponse:
    headers = {
        "Cache-Control": 'no-cache, no-store'
    }
    return JSONResponse(
        {
            'detail': 'Request processing time excedeed limit',
        },
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        headers=headers
    )
