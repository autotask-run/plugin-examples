import { createServer } from 'node:http';
import { COMMANDS, renderChecklist, renderDailyNote } from './template-engine.mjs';

const HOST = process.env.HOST || '0.0.0.0';
const PORT = Number(process.env.PORT || 8765);
const MAX_BODY_BYTES = 128 * 1024;
const MAX_SELECTION_BYTES = 100_000;
const sessionId = 'obsidian-note-template-session';

const toolHandlers = new Map([
  [COMMANDS[0].tool, (selection) => renderDailyNote(selection)],
  [COMMANDS[1].tool, (selection) => renderChecklist(selection)],
]);

const inputSchema = {
  type: 'object',
  properties: {
    commandId: { type: 'string', description: 'Descriptor command id.' },
    tool: { type: 'string', description: 'Descriptor tool name.' },
    mode: { type: 'string', enum: ['insert', 'replace'] },
    selection: { type: 'string', description: 'The current note selection only.' },
    traceId: { type: 'string', description: 'AutoTask trace id.' },
  },
  required: ['commandId', 'tool', 'mode', 'selection', 'traceId'],
  additionalProperties: false,
};

function jsonRpc(id, result) {
  return { jsonrpc: '2.0', id, result };
}

function jsonRpcError(id, code, message) {
  return { jsonrpc: '2.0', id, error: { code, message } };
}

function sendJson(response, status, body, headers = {}) {
  response.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
    ...headers,
  });
  response.end(JSON.stringify(body));
}

function sendEmpty(response, status = 202, headers = {}) {
  response.writeHead(status, headers);
  response.end();
}

async function readJson(request) {
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    const buffer = Buffer.from(chunk);
    size += buffer.length;
    if (size > MAX_BODY_BYTES) throw new Error('request body is too large');
    chunks.push(buffer);
  }
  try {
    return JSON.parse(Buffer.concat(chunks).toString('utf8'));
  } catch {
    throw new Error('invalid JSON');
  }
}

function validateCall(body) {
  const args = body?.params?.arguments;
  const name = body?.params?.name;
  if (body?.method !== 'tools/call' || typeof name !== 'string' || !toolHandlers.has(name)) {
    return { error: [-32602, 'unknown MCP tool'] };
  }
  if (!args || args.tool !== name || typeof args.commandId !== 'string' || typeof args.traceId !== 'string') {
    return { error: [-32602, 'invalid note editor arguments'] };
  }
  if (args.mode !== 'insert' && args.mode !== 'replace') {
    return { error: [-32602, 'mode must be insert or replace'] };
  }
  if (typeof args.selection !== 'string' || Buffer.byteLength(args.selection, 'utf8') > MAX_SELECTION_BYTES) {
    return { error: [-32602, 'selection exceeds the 100000-byte limit'] };
  }
  if (args.selection.includes('\u0000')) {
    return { error: [-32602, 'selection contains a NUL byte'] };
  }
  return { args, name };
}

async function handleMcp(request, response) {
  if (request.method === 'DELETE') {
    sendEmpty(response, 202, { 'mcp-session-id': sessionId });
    return;
  }
  if (request.method !== 'POST') {
    sendJson(response, 405, { error: 'method not allowed' }, { allow: 'POST, DELETE' });
    return;
  }
  let body;
  try {
    body = await readJson(request);
  } catch (error) {
    sendJson(response, 400, { error: error instanceof Error ? error.message : 'invalid request' });
    return;
  }

  if (body.method === 'initialize') {
    sendJson(response, 200, jsonRpc(body.id, {
      protocolVersion: '2025-06-18',
      capabilities: { tools: {} },
      serverInfo: { name: 'autotask-obsidian-note-template', version: '1.0.0' },
    }), { 'mcp-session-id': sessionId });
    return;
  }
  if (body.method === 'notifications/initialized') {
    sendEmpty(response, 202, { 'mcp-session-id': sessionId });
    return;
  }
  if (body.method === 'tools/list') {
    sendJson(response, 200, jsonRpc(body.id, {
      tools: COMMANDS.map((command) => ({
        name: command.tool,
        description: `${command.name}。支持中文别名：${command.aliases.join('、')}。`,
        inputSchema,
      })),
    }), { 'mcp-session-id': sessionId });
    return;
  }
  if (body.method !== 'tools/call') {
    sendJson(response, 404, jsonRpcError(body.id, -32601, 'method not found'));
    return;
  }

  const call = validateCall(body);
  if (call.error) {
    sendJson(response, 400, jsonRpcError(body.id, call.error[0], call.error[1]), { 'mcp-session-id': sessionId });
    return;
  }
  try {
    const text = toolHandlers.get(call.name)(call.args.selection);
    const proposal = { kind: 'replace_selection.v1', text };
    sendJson(response, 200, jsonRpc(body.id, {
      content: [{ type: 'text', text: JSON.stringify(proposal) }],
      structuredContent: proposal,
      isError: false,
    }), { 'mcp-session-id': sessionId });
  } catch (error) {
    sendJson(response, 422, jsonRpcError(body.id, -32000, error instanceof Error ? error.message : 'tool failed'), { 'mcp-session-id': sessionId });
  }
}

const server = createServer(async (request, response) => {
  const pathname = new URL(request.url || '/', `http://${request.headers.host || 'localhost'}`).pathname;
  if (request.method === 'GET' && pathname === '/health') {
    sendJson(response, 200, { status: 'ok', service: 'obsidian-note-template' });
    return;
  }
  if (pathname.endsWith('/mcp')) {
    await handleMcp(request, response);
    return;
  }
  sendJson(response, 404, { error: 'not found' });
});

server.listen(PORT, HOST, () => {
  const address = server.address();
  const port = typeof address === 'object' && address ? address.port : PORT;
  console.log(`READY http://${HOST}:${port}/mcp`);
});

function close() {
  server.close(() => process.exit(0));
}
process.on('SIGTERM', close);
process.on('SIGINT', close);
