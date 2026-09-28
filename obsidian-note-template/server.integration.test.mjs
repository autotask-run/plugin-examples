import { once } from 'node:events';
import { spawn } from 'node:child_process';
import { test } from 'node:test';
import assert from 'node:assert/strict';

async function startServer() {
  const child = spawn(process.execPath, ['server.mjs'], {
    cwd: new URL('.', import.meta.url),
    env: { ...process.env, HOST: '127.0.0.1', PORT: '0', NOTE_TEMPLATE_TIME_ZONE: 'Asia/Shanghai' },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  let output = '';
  const port = await new Promise((resolve, reject) => {
    const onData = (chunk) => {
      output += chunk.toString();
      const match = output.match(/READY http:\/\/127\.0\.0\.1:(\d+)\/mcp/);
      if (match) resolve(Number(match[1]));
    };
    child.stdout.on('data', onData);
    child.stderr.on('data', (chunk) => { output += chunk.toString(); });
    child.once('error', reject);
    child.once('exit', (code) => {
      if (code !== null && code !== 0) reject(new Error(`server exited ${code}: ${output}`));
    });
  });
  return { child, base: `http://127.0.0.1:${port}` };
}

async function post(base, body) {
  const response = await fetch(`${base}/mcp`, {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'content-type': 'application/json' },
  });
  return { response, body: await response.json() };
}

test('serves health and the initialize/list/call lifecycle', async () => {
  const { child, base } = await startServer();
  try {
    const health = await fetch(`${base}/health`);
    assert.equal(health.status, 200);
    assert.deepEqual(await health.json(), { status: 'ok', service: 'obsidian-note-template' });

    const initialize = await post(base, { id: 1, method: 'initialize', params: {} });
    assert.equal(initialize.response.status, 200);
    assert.equal(initialize.body.result.serverInfo.name, 'autotask-obsidian-note-template');

    const listed = await post(base, { id: 2, method: 'tools/list', params: {} });
    assert.deepEqual(
      listed.body.result.tools.map(({ name }) => name),
      ['obsidian.note-template.daily', 'obsidian.note-template.checklist'],
    );

    const called = await post(base, {
      id: 3,
      method: 'tools/call',
      params: {
        name: 'obsidian.note-template.checklist',
        arguments: {
          commandId: 'selection-checklist',
          tool: 'obsidian.note-template.checklist',
          mode: 'replace',
          selection: '梳理发布清单\n- [x] 通知团队',
          traceId: 'service-test',
        },
      },
    });
    assert.equal(called.response.status, 200);
    assert.deepEqual(called.body.result.structuredContent, {
      kind: 'replace_selection.v1',
      text: '- [ ] 梳理发布清单\n- [ ] 通知团队',
    });
  } finally {
    child.kill('SIGTERM');
    await once(child, 'exit');
  }
});

test('rejects NUL input and unknown tools', async () => {
  const { child, base } = await startServer();
  try {
    const unknown = await post(base, {
      id: 4,
      method: 'tools/call',
      params: { name: 'unknown', arguments: {} },
    });
    assert.equal(unknown.response.status, 400);
    assert.equal(unknown.body.error.code, -32602);

    const nul = await post(base, {
      id: 5,
      method: 'tools/call',
      params: {
        name: 'obsidian.note-template.daily',
        arguments: {
          commandId: 'daily-note-template',
          tool: 'obsidian.note-template.daily',
          mode: 'insert',
          selection: 'bad\u0000input',
          traceId: 'service-test',
        },
      },
    });
    assert.equal(nul.response.status, 400);
    assert.equal(nul.body.error.code, -32602);
  } finally {
    child.kill('SIGTERM');
    await once(child, 'exit');
  }
});
