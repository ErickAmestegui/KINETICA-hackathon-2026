"""Offline-testable SAM boundary. Never serialize raw parser diagnostics or exceptions."""
import json
import uuid
from dataclasses import asdict

import httpx
from meta_sam_parser import parse_responses_stream, video_segmentation_format, decode_mask_to_svg_path

SAM_ERROR_CODES = frozenset({
    'stream_consumed', 'stream_aborted', 'response_failed', 'response_error',
    'response_lane', 'response_refusal', 'parser_error', 'source_error', 'invalid_mask_payload',
})
EVENT_TYPES = frozenset({
    'response.created', 'response.in_progress', 'response.output_item.added',
    'response.content_part.added', 'response.output_text.delta', 'response.output_text.done',
    'response.content_part.done', 'response.output_item.done', 'response.completed',
    'response.incomplete', 'response.failed', 'error',
})
FORMAT_CODES = frozenset({'ignored_field', 'ignored_confidence', 'ignored_token',
                          'malformed_record', 'invalid_frame', 'unexpected_frame',
                          'invalid_box', 'invalid_mask_size', 'invalid_mask_payload'})


class SamBoundaryError(Exception):
    def __init__(self, category, http_status=None):
        super().__init__(category)
        self.category = category
        self.http_status = http_status


def new_diagnostic():
    return {'id': uuid.uuid4().hex[:12], 'phase': 'file_upload', 'events': 0,
            'bytes': 0, 'last_event': None}


def failure_info(exc, phase):
    """Inspect bounded cause chains by type/code only, never message/event/body/URL."""
    chain, current = [], exc
    while isinstance(current, BaseException) and len(chain) < 8 and current not in chain:
        chain.append(current)
        current = getattr(current, 'cause', None) or current.__cause__
    parser_code = next((e.code for e in chain if getattr(e, 'code', None) in SAM_ERROR_CODES), None)
    category, status = 'internal_error', None
    for e in reversed(chain):
        if isinstance(e, SamBoundaryError):
            category, status = e.category, e.http_status
        elif isinstance(e, httpx.TimeoutException): category = 'timeout'
        elif isinstance(e, httpx.ConnectError): category = 'connection'
        elif isinstance(e, (httpx.ReadError, httpx.RemoteProtocolError)): category = 'disconnection'
        elif isinstance(e, httpx.HTTPError): category = 'transport'
        elif getattr(e, 'code', None) in SAM_ERROR_CODES:
            if category == 'internal_error':
                category = {'response_failed': 'response_failed', 'response_error': 'response_error',
                            'response_refusal': 'refusal', 'invalid_mask_payload': 'mask_decode'}.get(e.code, 'parser')
        elif isinstance(e, (ValueError, TypeError, KeyError)) and category == 'internal_error':
            category = 'mask_decode' if phase == 'mask_decode' else 'parser'
    if category == 'parser': phase = 'parser'
    return {'phase': phase, 'category': category, 'http_status': status, 'parser_code': parser_code}


def log_sam_failure(diagnostic):
    # This object is constructed locally from counters, enums and a random local ID.
    # No remote IDs, filenames, headers, usage bodies, exception text or masks.
    print('SAM_DIAGNOSTIC ' + json.dumps(diagnostic, sort_keys=True), flush=True)


def check_sam_http(response):
    if not response.is_success:
        raise SamBoundaryError('http', response.status_code)


async def sse_events(response, diagnostic, usage):
    """Bounded UTF-8 SSE framing, including split CRLF/multiline data and final EOF."""
    import codecs
    decoder = codecs.getincrementaldecoder('utf-8')('strict')
    buffer, data = '', []
    size_limit = 64 * 1024 * 1024

    def event(payload):
        try:
            value = json.loads(payload)
        except (ValueError, TypeError):
            raise SamBoundaryError('sse_json') from None
        if not isinstance(value, dict) or not isinstance(value.get('type'), str):
            raise SamBoundaryError('sse_event_shape')
        kind = value['type']
        diagnostic['events'] += 1
        diagnostic['last_event'] = kind if kind in EVENT_TYPES else 'other'
        if kind in ('response.completed', 'response.incomplete', 'response.failed'):
            raw = value.get('response', {})
            raw = raw.get('usage', {}) if isinstance(raw, dict) else {}
            # Usage may evolve: only known numeric fields cross our boundary.
            if isinstance(raw, dict):
                for key in ('input_tokens', 'output_tokens', 'total_tokens', 'video_frames_processed', 'images_processed'):
                    n = raw.get(key)
                    if isinstance(n, int) and not isinstance(n, bool) and n >= 0:
                        usage[key] = n
        return value

    async def chunks():
        try:
            async for raw in response.aiter_bytes():
                diagnostic['bytes'] += len(raw)
                if diagnostic['bytes'] > size_limit:
                    raise SamBoundaryError('response_size_limit')
                yield decoder.decode(raw)
            yield decoder.decode(b'', final=True)
        except UnicodeDecodeError:
            raise SamBoundaryError('sse_encoding') from None

    async for chunk in chunks():
        buffer += chunk
        # CR, LF and CRLF are SSE line endings. Hold a trailing CR across chunks.
        while True:
            ends = [i for i in (buffer.find('\r'), buffer.find('\n')) if i >= 0]
            if not ends: break
            i = min(ends)
            if buffer[i:] == '\r': break
            line = buffer[:i]
            count = 2 if buffer[i:i+2] == '\r\n' else 1
            buffer = buffer[i+count:]
            if line.startswith('data:'):
                data.append(line[5:].removeprefix(' '))
            elif not line and data:
                payload, data = '\n'.join(data), []
                if payload == '[DONE]': return
                yield event(payload)
    # EOF cannot fabricate a completed event. A final data field is still parsed.
    line = buffer.rstrip('\r')
    if line.startswith('data:'): data.append(line[5:].removeprefix(' '))
    if data and '\n'.join(data) != '[DONE]':
        yield event('\n'.join(data))


async def parse_sam(events, diagnostic=None):
    diagnostic = diagnostic if diagnostic is not None else new_diagnostic()
    diagnostic['phase'] = 'parser'
    parsed = parse_responses_stream(events, video_segmentation_format())
    view, failure = None, None
    try:
        # Snapshots are cumulative: replace, never append snapshots together.
        async for snapshot in parsed:
            view = snapshot
        view = await parsed.final_result()
        outcome = {'status': view.outcome.status}
        if view.outcome.status == 'incomplete':
            outcome['reason'] = view.outcome.reason
            failure = {'phase': 'response_stream', 'category': 'premature_eof' if view.outcome.reason == 'eof' else 'response_incomplete',
                       'http_status': None, 'parser_code': None}
    except Exception as exc:
        failure = failure_info(exc, diagnostic['phase'])
        outcome = {'status': 'failed', 'reason': failure['category']}

    records, diagnostics = [], []
    if view is not None:
        # Diagnostic codes/severities are mapped, not arbitrary upstream strings.
        for d in view.diagnostics:
            diagnostics.append({'code': d.code if d.code in FORMAT_CODES else 'format_diagnostic', 'line': d.line,
                                'severity': d.severity if d.severity in ('warning', 'error', 'info') else 'warning'})
        for row in view.records:
            if row.kind not in ('box', 'mask'): continue
            record = {'kind': row.kind, 'object_id': row.object_id,
                      'frame': row.frame.frame_index if row.frame else 0, 'confidence': row.confidence}
            if row.kind == 'box':
                record.update(left=row.left, top=row.top, right=row.right, bottom=row.bottom)
            else:
                try:
                    record.update(path=decode_mask_to_svg_path(row.mask), bounds=asdict(row.bounds),
                                  width=row.mask.width, height=row.mask.height)
                except Exception as exc:
                    failure = failure_info(exc, 'mask_decode')
                    outcome = {'status': 'failed', 'reason': 'mask_decode'}
                    continue
            records.append(record)
    return {'records': records, 'outcome': outcome, 'failure': failure,
            'diagnostics': diagnostics, 'reconstruction_verified': False,
            'provenance': 'Meta sam-3.1 response parsed by official meta-sam-parser 0.1.0'}
