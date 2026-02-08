"""
Decorators for Dify Workflow Generator.

Provides useful decorators for common patterns.
"""

import functools
import time
from typing import Callable, Any

from .logging_config import get_logger

logger = get_logger("decorators")


def log_execution(func: Callable) -> Callable:
    """
    Decorator to log function execution time and result.
    
    Example:
        @log_execution
        def my_function():
            return "result"
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.debug(f"Starting {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(f"Completed {func.__name__} in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed {func.__name__} in {elapsed:.3f}s: {e}")
            raise
    
    return wrapper


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator to retry a function on error.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        exceptions: Tuple of exceptions to catch
        
    Example:
        @retry_on_error(max_retries=3, delay=1.0)
        def api_call():
            return requests.get("https://api.example.com")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (attempt + 1)
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {wait_time:.1f}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries} attempts")
            
            raise last_exception
        
        return wrapper
    return decorator


def deprecated(alternative: str = None) -> Callable:
    """
    Decorator to mark functions as deprecated.
    
    Args:
        alternative: Name of the alternative function to use
        
    Example:
        @deprecated(alternative="new_function")
        def old_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            msg = f"{func.__name__} is deprecated"
            if alternative:
                msg += f". Use {alternative} instead"
            logger.warning(msg)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_input(validator: Callable[[Any], bool], error_msg: str = "Invalid input") -> Callable:
    """
    Decorator to validate function input.
    
    Args:
        validator: Function that takes input and returns True/False
        error_msg: Error message to raise on validation failure
        
    Example:
        @validate_input(lambda x: x > 0, "Value must be positive")
        def process_positive(value):
            return value * 2
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Validate first positional argument
            if args:
                if not validator(args[0]):
                    raise ValueError(error_msg)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def singleton(cls):
    """
    Decorator to make a class a singleton.
    
    Example:
        @singleton
        class MyClass:
            pass
    """
    instances = {}
    
    @functools.wraps(cls)
    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return wrapper


def memoize(func: Callable) -> Callable:
    """
    Decorator to cache function results.
    
    Example:
        @memoize
        def expensive_computation(n):
            return n * n
    """
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    
    return wrapper
