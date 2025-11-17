"""
Utility decorators for error handling, retry logic, and performance monitoring.
"""
import time
import functools
from typing import Callable, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .logger import log


def timeit(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.

    Args:
        func: Function to measure

    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        log.debug(f"{func.__name__} took {execution_time:.4f} seconds")
        return result
    return wrapper


def handle_exceptions(default_return: Any = None, log_error: bool = True):
    """
    Decorator to handle exceptions gracefully.

    Args:
        default_return: Value to return on exception
        log_error: Whether to log the error

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    log.error(f"Error in {func.__name__}: {str(e)}")
                    log.exception(e)
                return default_return
        return wrapper
    return decorator


def retry_on_failure(
    max_attempts: int = 3,
    wait_min: int = 1,
    wait_max: int = 10,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry function on failure with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        wait_min: Minimum wait time in seconds
        wait_max: Maximum wait time in seconds
        exceptions: Tuple of exceptions to catch

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=wait_min, max=wait_max),
            retry=retry_if_exception_type(exceptions),
            reraise=True
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                log.warning(f"Retrying {func.__name__} due to: {str(e)}")
                raise
        return wrapper
    return decorator


def rate_limit(calls: int = 10, period: int = 60):
    """
    Decorator to rate limit function calls.

    Args:
        calls: Number of calls allowed
        period: Time period in seconds

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        call_times = []

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal call_times
            now = time.time()

            # Remove calls outside the time window
            call_times = [t for t in call_times if now - t < period]

            if len(call_times) >= calls:
                sleep_time = period - (now - call_times[0])
                log.warning(f"Rate limit reached for {func.__name__}. Sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
                call_times = []

            call_times.append(now)
            return func(*args, **kwargs)

        return wrapper
    return decorator


def cache_result(ttl: int = 300):
    """
    Decorator to cache function results with TTL.

    Args:
        ttl: Time to live in seconds

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        cache = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = str(args) + str(sorted(kwargs.items()))
            now = time.time()

            # Check if cached and not expired
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl:
                    log.debug(f"Cache hit for {func.__name__}")
                    return result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache[key] = (result, now)

            # Clean old cache entries
            cache_cleanup = {
                k: v for k, v in cache.items()
                if now - v[1] < ttl
            }
            cache.clear()
            cache.update(cache_cleanup)

            return result

        return wrapper
    return decorator


def validate_params(**validations):
    """
    Decorator to validate function parameters.

    Args:
        **validations: Validation functions for each parameter

    Returns:
        Decorator function

    Example:
        @validate_params(price=lambda x: x > 0, quantity=lambda x: x > 0)
        def place_order(price, quantity):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate parameters
            for param_name, validator in validations.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise ValueError(
                            f"Invalid value for parameter '{param_name}': {value}"
                        )

            return func(*args, **kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test decorators

    @timeit
    def slow_function():
        time.sleep(1)
        return "Done"

    @handle_exceptions(default_return=0)
    def error_function():
        raise ValueError("Test error")

    @retry_on_failure(max_attempts=3)
    def flaky_function(should_fail: bool = True):
        if should_fail:
            raise ConnectionError("Connection failed")
        return "Success"

    @validate_params(price=lambda x: x > 0, quantity=lambda x: x > 0)
    def place_order(price: float, quantity: float):
        return f"Order placed: {price} x {quantity}"

    # Test
    print("Testing decorators...")
    print(slow_function())
    print(error_function())
    try:
        print(place_order(100, 0.5))
        print(place_order(-100, 0.5))  # Should raise ValueError
    except ValueError as e:
        print(f"Caught: {e}")

    print("✅ Decorators test complete")
