# Built-in Dependencies
from typing import Any
import threading
import asyncio
import atexit
import os

# Third-Party Dependencies
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
)
import httpx

# Local Dependencies
from src.core.logger import logger_httpx

# Default retry wait configuration: exponential backoff starting at 2s, up to 10s, multiplier 1
WAIT_CONFIG = wait_exponential(multiplier=1, min=2, max=10)

_DEFAULT_TIMEOUT = 50.0

_thread_local = threading.local()


def _reset_client_after_fork():
    if hasattr(_thread_local, "client"):
        _thread_local.client = None


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_reset_client_after_fork)


def get_global_client() -> httpx.AsyncClient:
    if not hasattr(_thread_local, "client") or _thread_local.client is None:
        # Create a new client for this specific thread and its event loop
        _thread_local.client = httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT)
    return _thread_local.client


async def close_global_client() -> None:
    if hasattr(_thread_local, "client") and _thread_local.client is not None:
        try:
            await _thread_local.client.aclose()
        finally:
            _thread_local.client = None


def _close_client_sync():
    """Close the client synchronously for use with atexit"""
    if not hasattr(_thread_local, "client") or _thread_local.client is None:
        return

    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If the loop is running, create a task to close the client
            asyncio.create_task(close_global_client())
        else:
            # If the loop is not running, run the close function synchronously
            loop.run_until_complete(close_global_client())
    except RuntimeError:
        # If there is no event loop, just run the close function synchronously
        asyncio.run(close_global_client())


# Register the synchronous close function to be called on program exit (works with Celery and Jupyter)
atexit.register(_close_client_sync)


class BadRequestException(Exception):
    """Exception raised when the server returns a 400 Bad Request response."""

    pass


def extract_error_message(response: httpx.Response) -> str:
    """
    Extract error message from various common response structures.

    Parameters
    ----------
    response : httpx.Response
        HTTP response object to extract error message from

    Returns
    -------
    str
        Extracted error message text
    """
    try:
        data = response.json()
        if isinstance(data, dict):
            return (
                data.get("error", {}).get("message")
                or data.get("message")
                or data.get("detail")
                or str(data)
            )
        return str(data)
    except Exception:
        return response.text


def raise_for_status(response: httpx.Response) -> None:
    """
    Inspect HTTP response and raise appropriate exceptions for error status codes.

    Parameters
    ----------
    response : httpx.Response
        HTTP response object to inspect

    Raises
    ------
    BadRequestException
        For 400 Bad Request responses
    httpx.HTTPStatusError
        For other HTTP error status codes (4xx/5xx)
    """
    if response.status_code == 400:
        response_message = extract_error_message(response=response)
        raise BadRequestException(f"400 Bad Request: {response_message}")

    response.raise_for_status()


def should_retry(exception: BaseException) -> bool:
    """
    Determine if a request should be retried based on exception type.

    Parameters
    ----------
    exception : BaseException
        Exception to evaluate for retry

    Returns
    -------
    bool
        True if request should be retried, False otherwise

    Notes
    -----
    - Retries for network errors and transient failures
    - BadRequestException is not retried (client error)
    """
    return isinstance(exception, (httpx.TimeoutException, httpx.RequestError))


def _log_response_debug(response: httpx.Response) -> None:
    """
    Log response content in debug mode.

    Parameters
    ----------
    response : httpx.Response
        HTTP response object to log
    """
    try:
        logger_httpx.debug(f"Response Status: {response.status_code} | Content: {response.json()}")
    except Exception:
        logger_httpx.debug(f"Response Status: {response.status_code} | Content: {response.text}")


@retry(
    stop=stop_after_attempt(5),
    wait=WAIT_CONFIG,
    retry=retry_if_exception(should_retry),
)
async def make_get_request(
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    cookies: dict | None = None,
    auth: Any = httpx.USE_CLIENT_DEFAULT,
    follow_redirects: bool = False,
    timeout: httpx.Timeout | None = None,
    debug_mode: bool = False,
) -> httpx.Response:
    """
    Perform async GET request with retry logic for transient errors.

    Parameters
    ----------
    url : str
        Target URL for GET request
    params : dict, optional
        Query parameters to include in request
    headers : dict, optional
        HTTP headers to send with request
    cookies : dict, optional
        Cookies to include with request
    auth : httpx.Auth, optional
        Authentication class to use
    follow_redirects : bool, optional
        Whether to follow redirects. Defaults to False.
    timeout : httpx.Timeout, optional
        Timeout configuration for the request
    debug_mode : bool, optional
        Enable debug output (logs response content)

    Returns
    -------
    httpx.Response
        HTTP response object

    Raises
    ------
    BadRequestException
        For 400 Bad Request errors
    httpx.HTTPStatusError
        For other HTTP errors (4xx/5xx)
    httpx.RequestError
        For persistent network issues after retries
    """
    client = get_global_client()
    response = await client.get(
        url,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        follow_redirects=follow_redirects,
        timeout=timeout,
    )

    if debug_mode:
        _log_response_debug(response)

    raise_for_status(response)
    return response


@retry(
    stop=stop_after_attempt(5),
    wait=WAIT_CONFIG,
    retry=retry_if_exception(should_retry),
)
async def make_post_request(
    url: str,
    headers: dict | None = None,
    json: dict | None = None,
    data: dict | None = None,
    cookies: dict | None = None,
    auth: Any = httpx.USE_CLIENT_DEFAULT,
    follow_redirects: bool = False,
    timeout: httpx.Timeout | None = None,
    debug_mode: bool = False,
) -> httpx.Response:
    """
    Perform async POST request with retry logic for transient errors.

    Parameters
    ----------
    url : str
        Target URL for POST request
    headers : dict, optional
        HTTP headers to send with request
    json : dict, optional
        JSON-serializable data for request body
    data : dict, optional
        Form data or alternative body payload
    cookies : dict, optional
        Cookies to include with request
    auth : httpx.Auth, optional
        Authentication class to use
    follow_redirects : bool, optional
        Whether to follow redirects. Defaults to False.
    timeout : httpx.Timeout, optional
        Timeout configuration for the request
    debug_mode : bool, optional
        Enable debug output (logs response content)

    Returns
    -------
    httpx.Response
        HTTP response object

    Raises
    ------
    BadRequestException
        For 400 Bad Request errors
    httpx.HTTPStatusError
        For other HTTP errors (4xx/5xx)
    httpx.RequestError
        For persistent network issues after retries
    """
    client = get_global_client()
    response = await client.post(
        url,
        headers=headers,
        json=json,
        data=data,
        cookies=cookies,
        auth=auth,
        follow_redirects=follow_redirects,
        timeout=timeout,
    )

    if debug_mode:
        _log_response_debug(response)

    raise_for_status(response)
    return response


@retry(
    stop=stop_after_attempt(5),
    wait=WAIT_CONFIG,
    retry=retry_if_exception(should_retry),
)
async def make_delete_request(
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
    cookies: dict | None = None,
    auth: Any = httpx.USE_CLIENT_DEFAULT,
    follow_redirects: bool = False,
    timeout: httpx.Timeout | None = None,
    debug_mode: bool = False,
) -> httpx.Response:
    """
    Perform async DELETE request with retry logic for transient errors.

    Parameters
    ----------
    url : str
        Target URL for DELETE request
    params : dict, optional
        Query parameters to include in the URL
    headers : dict, optional
        HTTP headers to send with request
    cookies : dict, optional
        Cookies to include with request
    auth : httpx.Auth, optional
        Authentication class to use
    follow_redirects : bool, optional
        Whether to follow redirects. Defaults to False.
    timeout : httpx.Timeout, optional
        Timeout configuration for the request
    debug_mode : bool, optional
        Enable debug output (logs response content)

    Returns
    -------
    httpx.Response
        HTTP response object

    Raises
    ------
    BadRequestException
        For 400 Bad Request errors
    httpx.HTTPStatusError
        For other HTTP errors (4xx/5xx)
    httpx.RequestError
        For persistent network issues after retries
    """
    client = get_global_client()
    response = await client.delete(
        url,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        follow_redirects=follow_redirects,
        timeout=timeout,
    )

    if debug_mode:
        _log_response_debug(response)

    raise_for_status(response)
    return response


@retry(
    stop=stop_after_attempt(5),
    wait=WAIT_CONFIG,
    retry=retry_if_exception(should_retry),
)
async def make_put_request(
    url: str,
    headers: dict | None = None,
    json: dict | None = None,
    data: dict | None = None,
    cookies: dict | None = None,
    auth: Any = httpx.USE_CLIENT_DEFAULT,
    follow_redirects: bool = False,
    timeout: httpx.Timeout | None = None,
    debug_mode: bool = False,
) -> httpx.Response:
    """
    Perform async PUT request with retry logic for transient errors.

    Parameters
    ----------
    url : str
        Target URL for PUT request
    headers : dict, optional
        HTTP headers to send with request
    json : dict, optional
        JSON-serializable data for request body
    data : dict, optional
        Form data or alternative body payload
    cookies : dict, optional
        Cookies to include with request
    auth : httpx.Auth, optional
        Authentication class to use
    follow_redirects : bool, optional
        Whether to follow redirects. Defaults to False.
    timeout : httpx.Timeout, optional
        Timeout configuration for the request
    debug_mode : bool, optional
        Enable debug output (logs response content)

    Returns
    -------
    httpx.Response
        HTTP response object

    Raises
    ------
    BadRequestException
        For 400 Bad Request errors
    httpx.HTTPStatusError
        For other HTTP errors (4xx/5xx)
    httpx.RequestError
        For persistent network issues after retries
    """
    client = get_global_client()
    response = await client.put(
        url,
        headers=headers,
        json=json,
        data=data,
        cookies=cookies,
        auth=auth,
        follow_redirects=follow_redirects,
        timeout=timeout,
    )

    if debug_mode:
        _log_response_debug(response)

    raise_for_status(response)
    return response


@retry(
    stop=stop_after_attempt(5),
    wait=WAIT_CONFIG,
    retry=retry_if_exception(should_retry),
)
async def make_patch_request(
    url: str,
    headers: dict | None = None,
    json: dict | None = None,
    data: dict | None = None,
    cookies: dict | None = None,
    auth: Any = httpx.USE_CLIENT_DEFAULT,
    follow_redirects: bool = False,
    timeout: httpx.Timeout | None = None,
    debug_mode: bool = False,
) -> httpx.Response:
    """
    Perform async PATCH request with retry logic for transient errors.

    Parameters
    ----------
    url : str
        Target URL for PATCH request
    headers : dict, optional
        HTTP headers to send with request
    json : dict, optional
        JSON-serializable data for request body
    data : dict, optional
        Form data or alternative body payload
    cookies : dict, optional
        Cookies to include with request
    auth : httpx.Auth, optional
        Authentication class to use
    follow_redirects : bool, optional
        Whether to follow redirects. Defaults to False.
    timeout : httpx.Timeout, optional
        Timeout configuration for the request
    debug_mode : bool, optional
        Enable debug output (logs response content)

    Returns
    -------
    httpx.Response
        HTTP response object

    Raises
    ------
    BadRequestException
        For 400 Bad Request errors
    httpx.HTTPStatusError
        For other HTTP errors (4xx/5xx)
    httpx.RequestError
        For persistent network issues after retries
    """
    client = get_global_client()
    response = await client.patch(
        url,
        headers=headers,
        json=json,
        data=data,
        cookies=cookies,
        auth=auth,
        follow_redirects=follow_redirects,
        timeout=timeout,
    )

    if debug_mode:
        _log_response_debug(response)

    raise_for_status(response)
    return response
