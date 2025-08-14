"""Retry utilities for reliable data operations.

This module provides composable retry patterns integrated with Result types
for handling transient failures in data source operations.
"""

from typing import Callable, TypeVar, Any, Optional
from functools import wraps
import time

from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
from loguru import logger

from logerr import Result
from logerr.utils import execute
from autoframe.types import DataSourceError, ConfigurationError

T = TypeVar('T')
R = TypeVar('R')


# Common retry configurations
DATABASE_RETRY = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
    before_sleep=before_sleep_log(logger, 20),
    after=after_log(logger, 20)
)

NETWORK_RETRY = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, 20)
)

QUICK_RETRY = retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=0.2, min=0.1, max=1),
    before_sleep=before_sleep_log(logger, 30)
)


def with_database_retry(func: Callable[[], T]) -> Callable[[], Result[T, DataSourceError]]:
    """Apply database retry logic to a function returning Result types.
    
    Args:
        func: Function to wrap with retry logic
        
    Returns:
        Function that executes with retry and returns Result
        
    Examples:
        >>> @with_database_retry
        ... def connect_to_db():
        ...     return client.connect()
        >>> 
        >>> result = connect_to_db()
        >>> if result.is_ok():
        ...     print("Connected successfully")
    """
    @wraps(func)
    def wrapper() -> Result[T, DataSourceError]:
        @DATABASE_RETRY
        def retry_func():
            return func()
        
        return execute(retry_func).map_err(
            lambda e: DataSourceError(f"Operation failed after retries: {str(e)}")
        )
    
    return wrapper


def with_network_retry(func: Callable[[], T]) -> Callable[[], Result[T, DataSourceError]]:
    """Apply network retry logic to a function.
    
    Args:
        func: Function to wrap with network retry logic
        
    Returns:
        Function that executes with retry and returns Result
    """
    @wraps(func)
    def wrapper() -> Result[T, DataSourceError]:
        @NETWORK_RETRY
        def retry_func():
            return func()
        
        return execute(retry_func).map_err(
            lambda e: DataSourceError(f"Network operation failed after retries: {str(e)}")
        )
    
    return wrapper


def with_quick_retry(func: Callable[[], T]) -> Callable[[], Result[T, Any]]:
    """Apply quick retry logic for fast operations.
    
    Args:
        func: Function to wrap with quick retry logic
        
    Returns:
        Function that executes with retry and returns Result
    """
    @wraps(func)
    def wrapper() -> Result[T, Any]:
        @QUICK_RETRY
        def retry_func():
            return func()
        
        return execute(retry_func)
    
    return wrapper


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0
) -> Callable[[Callable[[], T]], Callable[[], Result[T, Any]]]:
    """Create a custom retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Multiplier for exponential backoff
        
    Returns:
        Decorator function
        
    Examples:
        >>> @retry_with_backoff(max_attempts=5, base_delay=0.5)
        ... def fetch_data():
        ...     return api_client.get_data()
    """
    def decorator(func: Callable[[], T]) -> Callable[[], Result[T, Any]]:
        @wraps(func)
        def wrapper() -> Result[T, Any]:
            last_result = None
            delay = base_delay
            
            for attempt in range(max_attempts):
                result = execute(func)
                
                if result.is_ok():
                    return result
                
                # Result is an error
                last_result = result
                
                if attempt < max_attempts - 1:  # Don't sleep on the last attempt
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed: {result.unwrap_err()}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
                else:
                    logger.error(f"All {max_attempts} attempts failed. Last error: {result.unwrap_err()}")
            
            # Return the last failed result
            return last_result
        
        return wrapper
    return decorator


def retry_on_condition(
    condition: Callable[[Exception], bool],
    max_attempts: int = 3,
    delay: float = 1.0
) -> Callable[[Callable[[], T]], Callable[[], Result[T, Any]]]:
    """Retry based on a custom condition.
    
    Args:
        condition: Function that returns True if the exception should trigger a retry
        max_attempts: Maximum number of retry attempts
        delay: Fixed delay between retries in seconds
        
    Returns:
        Decorator function
        
    Examples:
        >>> def should_retry(exc):
        ...     return isinstance(exc, ConnectionError) or "timeout" in str(exc).lower()
        >>> 
        >>> @retry_on_condition(should_retry, max_attempts=3)
        ... def unreliable_operation():
        ...     return make_request()
    """
    def decorator(func: Callable[[], T]) -> Callable[[], Result[T, Any]]:
        @wraps(func)
        def wrapper() -> Result[T, Any]:
            last_exception = None
            
            for attempt in range(max_attempts):
                result = execute(func)
                
                if result.is_ok():
                    return result
                
                exception = result.unwrap_err()
                last_exception = exception
                
                if attempt < max_attempts - 1 and condition(exception):
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed: {str(exception)}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    break
            
            return execute(lambda: (_ for _ in ()).throw(last_exception) if last_exception else None)
        
        return wrapper
    return decorator


# Predefined condition functions for common retry scenarios
def is_transient_error(exception: Exception) -> bool:
    """Check if an exception represents a transient error worth retrying.
    
    Args:
        exception: The exception to check
        
    Returns:
        True if the error is likely transient
    """
    transient_types = (ConnectionError, TimeoutError, OSError)
    if isinstance(exception, transient_types):
        return True
    
    error_msg = str(exception).lower()
    transient_keywords = [
        "timeout", "connection", "network", "temporary", 
        "unavailable", "busy", "overload", "rate limit"
    ]
    
    return any(keyword in error_msg for keyword in transient_keywords)


def is_database_error(exception: Exception) -> bool:
    """Check if an exception represents a database error worth retrying.
    
    Args:
        exception: The exception to check
        
    Returns:
        True if the error is a retryable database error
    """
    if isinstance(exception, (ConnectionError, TimeoutError)):
        return True
    
    error_msg = str(exception).lower()
    db_retry_keywords = [
        "connection", "timeout", "server", "network", 
        "unavailable", "lock", "deadlock", "transaction"
    ]
    
    return any(keyword in error_msg for keyword in db_retry_keywords)


# Functional helpers for working with Result types and retries
def retry_result(
    result_func: Callable[[], Result[T, R]], 
    max_attempts: int = 3,
    delay: float = 1.0
) -> Result[T, R]:
    """Retry a function that returns a Result type.
    
    Args:
        result_func: Function that returns a Result
        max_attempts: Maximum retry attempts
        delay: Delay between retries
        
    Returns:
        Result from the last successful attempt or final error
    """
    last_result = None
    
    for attempt in range(max_attempts):
        result = result_func()
        
        if result.is_ok():
            return result
        
        last_result = result
        
        if attempt < max_attempts - 1:
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
            time.sleep(delay)
    
    return last_result


def batch_with_retry(
    items: list[T],
    batch_func: Callable[[list[T]], Result[R, Any]],
    batch_size: int = 100,
    max_attempts: int = 3
) -> Result[list[R], Any]:
    """Process items in batches with retry logic.
    
    Args:
        items: List of items to process
        batch_func: Function to process each batch
        batch_size: Size of each batch
        max_attempts: Retry attempts per batch
        
    Returns:
        Result containing list of batch results or error
    """
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        batch_result = retry_result(
            lambda: batch_func(batch),
            max_attempts=max_attempts
        )
        
        if batch_result.is_err():
            return batch_result
        
        results.append(batch_result.unwrap())
    
    return execute(lambda: results)