import {it,expect} from 'vitest';
import {failureMessage} from './api';
it('distinguishes unavailable usage from zero and omits unrelated private payloads',()=>{
 const value=failureMessage({diagnostic_id:'synthetic-only',category:'parser',phase:'tool_parser',http_status:200,usage:{prompt_tokens:200,completion_tokens:40},private_body:'SHOULD NEVER APPEAR'});
 expect(value).toContain('HTTP 200');expect(value).toContain('200 input / 40 output');expect(value).not.toContain('SHOULD NEVER APPEAR');
 expect(failureMessage({diagnostic_id:'synthetic-only',category:'connection',usage:{}})).toContain('usage unavailable');
});
