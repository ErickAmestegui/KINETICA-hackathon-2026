"""Synthetic wire events and HTTP mocks only; no operator secrets or Meta traffic."""
import asyncio
import json

import httpx
import pytest
from fastapi import HTTPException
from backend import sam_protocol

from backend import meta
from test_meta import EXAMPLE, events


def test_timeout_is_distinguished_through_official_parser():
    async def broken():
        async for event in events(EXAMPLE, complete=False):
            yield event
        raise httpx.ReadTimeout('PRIVATE-SENTINEL')
    result = asyncio.run(meta.parse_sam(broken()))
    assert result['outcome']['status'] == 'failed'
    assert result['failure']['category'] == 'timeout'
    assert result['failure']['parser_code'] == 'source_error'
    assert len(result['records']) == 2
    assert 'PRIVATE-SENTINEL' not in json.dumps(result)


def test_failed_response_is_explicit_and_safe():
    result = asyncio.run(meta.parse_sam(events(EXAMPLE, failed=True)))
    assert result['outcome']['status'] == 'failed'
    assert result['failure']['category'] == 'response_failed'
    assert result['reconstruction_verified'] is False


def test_eof_partial_is_not_verified():
    result = asyncio.run(meta.parse_sam(events(EXAMPLE, complete=False)))
    assert result['outcome'] == {'status': 'incomplete', 'reason': 'eof'}
    assert result['reconstruction_verified'] is False
    assert result['failure']['category'] == 'premature_eof'


class Fragments(httpx.AsyncByteStream):
    def __init__(self, payload, error=None):
        self.payload, self.error = payload, error

    async def __aiter__(self):
        for i in range(0, len(self.payload), 3):
            yield self.payload[i:i+3]
        if self.error:
            raise self.error


async def wire(terminal='completed', eof=False):
    parts = [b': local protocol fixture\r\n\r\n']
    async for value in events(EXAMPLE, complete=False):
        # JSON whitespace/newlines and UTF-8 characters split across network fragments.
        value['test_note'] = 'sintético'
        payload = json.dumps(value, ensure_ascii=False, indent=1)
        parts.append(('event: message\r\n' + '\r\n'.join('data: '+line for line in payload.splitlines())+'\r\n\r\n').encode())
    if terminal:
        event = {'type': 'response.'+terminal, 'response': {'usage': {'input_tokens': 50, 'video_frames_processed': 50, 'private': 'PRIVATE-SENTINEL'},
                 'incomplete_details': {'reason': 'PRIVATE-SENTINEL'}, 'error': {'message': 'PRIVATE-SENTINEL'}}}
        parts.append(('data: '+json.dumps(event)+('' if eof else '\r\n\r\n')).encode())
    return b''.join(parts)


def mock_segment(monkeypatch, tmp_path, *, terminal='completed', error=None,
                 upload_status=200, response_status=200, cleanup_status=200,
                 cleanup_error=None, upload_error=None, content_type='text/event-stream',
                 payload=None, eof=False, upload_json=None):
    """Only this local helper bypasses authorize, with a mandatory MockTransport.

    META_ALLOW_PAID stays false; global guards still prevent real HTTP transports.
    """
    calls = []
    content = payload if payload is not None else asyncio.run(wire(terminal, eof=eof))
    async def handle(request):
        calls.append((request.method, request.url.path))
        if request.url.path == '/v1/files':
            if upload_error: raise upload_error
            return httpx.Response(upload_status, json=upload_json if upload_json is not None else {'id': 'file-local-fixture'})
        if request.method == 'DELETE':
            if cleanup_error: raise cleanup_error
            return httpx.Response(cleanup_status, json={'private': 'PRIVATE-SENTINEL'})
        assert request.url.path == '/v1/responses'
        body = json.loads(request.content)
        assert body['model'] == 'sam-3.1' and body['stream'] is True
        assert body['metadata']['mask_encoding'] == 'one_bit'
        return httpx.Response(response_status, headers={'content-type': content_type},
                              stream=Fragments(content, error))
    real_client = httpx.AsyncClient
    monkeypatch.setattr(meta.httpx, 'AsyncClient', lambda **kwargs: real_client(transport=httpx.MockTransport(handle), **kwargs))
    monkeypatch.setattr(meta, 'authorize', lambda approved: None)
    monkeypatch.setattr(meta, 'headers', lambda: {'Authorization': 'Bearer MOCK-NOT-A-CREDENTIAL'})
    path = tmp_path/'synthetic-placeholder.mp4'
    path.write_bytes(b'local mock does not decode this file')
    try:
        result = asyncio.run(meta.segment(path, {'width':320,'height':334}, 'local fixture', [], True))
        http_status = 200
    except HTTPException as exc:
        result, http_status = exc.detail, exc.status_code
    assert meta.os.environ['META_ALLOW_PAID'] == 'false'
    assert calls.count(('POST','/v1/responses')) <= 1
    assert calls.count(('POST','/v1/files')) == 1
    assert calls.count(('DELETE','/v1/files/file-local-fixture')) <= 1
    return result, http_status, calls


@pytest.mark.parametrize('eof', [False, True])
def test_fragmented_utf8_crlf_multiline_valid_masks(monkeypatch, tmp_path, eof):
    result, code, calls = mock_segment(monkeypatch, tmp_path, eof=eof)
    assert code == 200 and result['outcome']['status'] == 'completed'
    assert len(result['records']) == 2 and result['records'][1]['path']
    assert result['usage'] == {'input_tokens': 50, 'video_frames_processed': 50}
    assert result['cleanup']['status'] == 'deleted'
    assert result['reconstruction_verified'] is False
    assert calls[-1][0] == 'DELETE'
    assert 'PRIVATE-SENTINEL' not in json.dumps(result)


@pytest.mark.parametrize('terminal,expected,reason', [
    ('incomplete','incomplete','response'), (None,'incomplete','eof'), ('failed','failed','response_failed'),
])
def test_partial_terminal_and_eof(monkeypatch, tmp_path, capsys, terminal, expected, reason):
    result, code, _ = mock_segment(monkeypatch, tmp_path, terminal=terminal)
    assert result['outcome'] == {'status': expected, 'reason': reason}
    assert code == (502 if expected == 'failed' else 200)
    assert len(result['records']) == 2
    assert result['cleanup']['status'] == 'deleted'
    assert 'PRIVATE-SENTINEL' not in json.dumps(result) + capsys.readouterr().out


@pytest.mark.parametrize('status', [400,401,402,403,429,500])
@pytest.mark.parametrize('phase', ['upload','stream'])
def test_http_error_categories_no_retries(monkeypatch, tmp_path, capsys, status, phase):
    result, code, calls = mock_segment(monkeypatch, tmp_path, **{('upload_status' if phase=='upload' else 'response_status'):status})
    assert code == 502
    assert result['failure']['category'] == 'http' and result['failure']['http_status'] == status
    assert result['cleanup']['status'] == ('not_needed' if phase=='upload' else 'deleted')
    assert result['retry_performed'] is False
    output = capsys.readouterr().out
    assert 'SAM_DIAGNOSTIC' in output
    assert all(s not in output for s in ('PRIVATE-SENTINEL', 'MOCK-NOT-A-CREDENTIAL', 'file-local-fixture', 'Authorization'))


@pytest.mark.parametrize('error,category', [
    (httpx.ReadTimeout('PRIVATE-SENTINEL'), 'timeout'),
    (httpx.ConnectError('PRIVATE-SENTINEL'), 'connection'),
    (httpx.ReadError('PRIVATE-SENTINEL'), 'disconnection'),
    (httpx.RemoteProtocolError('PRIVATE-SENTINEL'), 'disconnection'),
])
def test_broken_stream_preserves_accepted_partial_records(monkeypatch, tmp_path, capsys, error, category):
    result, code, _ = mock_segment(monkeypatch, tmp_path, terminal=None, error=error)
    assert code == 502 and result['failure']['category'] == category
    assert result['failure']['parser_code'] == 'source_error'
    assert len(result['records']) == 2 and result['cleanup']['status'] == 'deleted'
    assert 'PRIVATE-SENTINEL' not in json.dumps(result) + capsys.readouterr().out


def test_timeout_during_upload_acknowledgement(monkeypatch, tmp_path):
    result, code, calls = mock_segment(monkeypatch, tmp_path, upload_error=httpx.WriteTimeout('PRIVATE-SENTINEL'))
    assert code == 502 and result['failure']['category'] == 'timeout'
    assert result['cleanup']['status'] == 'unknown_upload'
    assert len(calls) == 1


@pytest.mark.parametrize('terminal', ['completed', 'failed'])
@pytest.mark.parametrize('cleanup_error', [None, httpx.ReadTimeout('PRIVATE-SENTINEL')])
def test_cleanup_failure_never_masks_primary_outcome(monkeypatch, tmp_path, terminal, cleanup_error):
    result, _, _ = mock_segment(monkeypatch, tmp_path, terminal=terminal, cleanup_status=503, cleanup_error=cleanup_error)
    assert result['outcome']['status'] == terminal
    assert result['cleanup']['status'] == 'failed'
    assert result['cleanup']['failure']['category'] == ('timeout' if cleanup_error else 'http')
    assert result['cleanup']['failure']['phase'] == 'remote_cleanup'


@pytest.mark.parametrize('payload,category', [
    (b'data: broken-json\n\n','sse_json'), (b'data: []\n\n','sse_event_shape'),
    (b'data: \xff\n\n','sse_encoding'),
])
def test_invalid_wire_is_safely_diagnosed(monkeypatch, tmp_path, payload, category):
    result, code, _ = mock_segment(monkeypatch, tmp_path, payload=payload)
    assert code == 502 and result['failure']['category'] == category
    assert result['cleanup']['status'] == 'deleted'


def test_wrong_content_type(monkeypatch, tmp_path):
    result, code, _ = mock_segment(monkeypatch, tmp_path, content_type='application/json')
    assert code == 502 and result['failure']['category'] == 'content_type'


def test_invalid_upload_contract_does_not_guess_remote_id(monkeypatch, tmp_path):
    result, code, calls = mock_segment(monkeypatch, tmp_path, upload_json={'id':'../PRIVATE-SENTINEL'})
    assert code == 502 and result['failure']['category'] == 'upload_contract'
    assert result['cleanup']['status'] == 'unknown_upload' and len(calls) == 1
    assert 'PRIVATE-SENTINEL' not in json.dumps(result)


def test_mask_conversion_failure_is_distinguished(monkeypatch):
    from meta_sam_parser import InvalidSegmentationMaskError
    def invalid(mask): raise InvalidSegmentationMaskError('PRIVATE-SENTINEL')
    monkeypatch.setattr(sam_protocol, 'decode_mask_to_svg_path', invalid)
    result = asyncio.run(meta.parse_sam(events(EXAMPLE)))
    assert result['outcome']['status'] == 'failed'
    assert result['failure']['category'] == 'mask_decode'
    assert result['failure']['phase'] == 'mask_decode'
    assert len(result['records']) == 1


def test_lane_error_is_parser_not_timeout():
    async def invalid():
        yield {'type':'response.completed'}  # No finalized text lane.
    result = asyncio.run(meta.parse_sam(invalid()))
    assert result['failure']['category'] == 'parser'
    assert result['failure']['parser_code'] == 'response_lane'


def test_done_marker_does_not_invent_completion(monkeypatch, tmp_path):
    result, _, _ = mock_segment(monkeypatch, tmp_path, payload=asyncio.run(wire(None))+b'data: [DONE]\n\n')
    assert result['outcome'] == {'status':'incomplete','reason':'eof'}


def test_real_entry_points_blocked_before_io(monkeypatch, tmp_path):
    monkeypatch.setenv('MODEL_API_KEY', 'MOCK-NOT-A-CREDENTIAL')
    def forbidden(**kwargs): raise AssertionError('Client must never be constructed')
    monkeypatch.setattr(meta.httpx, 'AsyncClient', forbidden)
    for coroutine in (meta.segment(tmp_path/'absent.mp4', {}, 'fixture', [], True),
                      meta.propose(tmp_path/'absent.mp4', {}, True)):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(coroutine)
        assert exc.value.status_code == 403


def test_default_network_transport_is_disabled():
    with pytest.raises(AssertionError, match='External network'):
        httpx.get('https://offline-test.invalid')
