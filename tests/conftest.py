"""Offline by construction: never inherit operator credentials or allow network I/O."""
import os
import socket

import httpx
import pytest

# Executed before backend.main loads dotenv. Empty values prevent dotenv fallback.
os.environ['MODEL_API_KEY'] = ''
os.environ['META_ALLOW_PAID'] = 'false'


@pytest.fixture(autouse=True)
def offline_only(monkeypatch):
    monkeypatch.setenv('MODEL_API_KEY', '')
    monkeypatch.setenv('META_ALLOW_PAID', 'false')

    def denied(*args, **kwargs):
        raise AssertionError('External network is forbidden in automated tests')

    async def async_denied(*args, **kwargs):
        denied()

    monkeypatch.setattr(httpx.HTTPTransport, 'handle_request', denied)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, 'handle_async_request', async_denied)
    # asyncio on Windows creates a loopback socket pair. Forbid non-loopback connects.
    original = socket.socket.connect
    def connect(sock, address):
        if not isinstance(address, tuple) or address[0] not in ('127.0.0.1', '::1'):
            denied()
        return original(sock, address)
    monkeypatch.setattr(socket.socket, 'connect', connect)
