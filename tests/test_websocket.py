import unittest
import asyncio
from time import time
from sys import platform
from parameterized import parameterized
import gsy_framework.client_connections.websocket_connection as websocket_connection
from gsy_framework.client_connections.websocket_connection import WebsocketAsyncConnection


class TestWebsocket(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.coro_backup = WebsocketAsyncConnection._connection_loop_coroutine
        WebsocketAsyncConnection._generate_websocket_connection_headers = lambda x: None
        websocket_connection.WEBSOCKET_WAIT_BEFORE_RETRY_SECONDS = 0
        websocket_connection.WEBSOCKET_MAX_CONNECTION_RETRIES = 5
        websocket_connection.WEBSOCKET_ERROR_THRESHOLD_SECONDS = 30

    @classmethod
    def tearDownClass(cls):
        WebsocketAsyncConnection._connection_loop_coroutine = cls.coro_backup

    @parameterized.expand(
        [(1, ),
         (3, ),
         (7, ),
         (13, )])
    def test_websocket_retries_the_connection_before_failing(self, num_of_retries):
        websocket_connection.WEBSOCKET_MAX_CONNECTION_RETRIES = num_of_retries
        coro_execution_counter = 0

        async def exception_raising_coroutine(s, _1):
            nonlocal coro_execution_counter
            coro_execution_counter += 1
            raise Exception("exception!")

        WebsocketAsyncConnection._connection_loop_coroutine = exception_raising_coroutine

        try:
            asyncio.get_event_loop().run_until_complete(
                WebsocketAsyncConnection(None, None, None).run_coroutine()
            )
        except Exception:
            pass
        else:
            # Asserting here because the retry_coroutine should not succeed
            assert False

        assert coro_execution_counter == num_of_retries + 1

    def test_websocket_conforms_to_wait_before_retry_parameter(self):
        websocket_connection.WEBSOCKET_WAIT_BEFORE_RETRY_SECONDS = 0.1

        async def exception_raising_coro(s, _1):
            raise Exception("exception!")

        WebsocketAsyncConnection._connection_loop_coroutine = exception_raising_coro

        start_time = time()
        try:
            asyncio.get_event_loop().run_until_complete(
                WebsocketAsyncConnection(None, None, None).run_coroutine()
            )
        except Exception:
            pass

        end_time = time()

        num_of_retries = websocket_connection.WEBSOCKET_MAX_CONNECTION_RETRIES
        expected_duration = 0.1 * (num_of_retries + 1)

        # On MacOS, the precision of asyncio.sleep is far worse than in Linux,
        # which has the result to not sleep the exact time it is dictated, but a bit more.
        # This test calls sleep multiple times which has the effect that deviations from
        # the sleep accumulate and can surpass the original
        # tolerance of 0.01. This is the reason for the explicit increased tolerance here.
        tolerance = 0.05 if platform == "darwin" else 0.01

        assert expected_duration <= end_time - start_time <= expected_duration + tolerance

    def test_websocket_restarts_the_retry_count_if_ws_coro_does_not_crash_for_some_time(self):
        websocket_connection.WEBSOCKET_ERROR_THRESHOLD_SECONDS = 0.1
        coro_execution_counter = 0

        async def exception_after_time_coro(s, _1):
            nonlocal coro_execution_counter
            coro_execution_counter += 1
            if coro_execution_counter < 4:
                await asyncio.sleep(0.12)
            raise Exception("exception!")

        WebsocketAsyncConnection._connection_loop_coroutine = exception_after_time_coro

        try:
            asyncio.get_event_loop().run_until_complete(
                WebsocketAsyncConnection(None, None, None).run_coroutine()
            )
        except Exception:
            pass

        assert coro_execution_counter == 8
