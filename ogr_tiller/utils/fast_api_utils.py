import functools
import signal
import sys

from fastapi.responses import JSONResponse
from starlette import status


class TimeOutException(Exception):
    """It took longer than expected"""


def abort_after(max_execution_time):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def handle_timeout(signum, frame):
                raise TimeOutException(f"Function execution took longer than {max_execution_time}s and was terminated")
            if sys.platform == 'win32':
                print("Won't be stopped in windows!")
            else:
                signal.signal(signal.SIGALRM, handle_timeout)
                signal.alarm(max_execution_time)
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
