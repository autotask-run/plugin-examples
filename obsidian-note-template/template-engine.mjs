const MAX_TEXT_BYTES = 100_000;

export const DEFAULT_TIME_ZONE = process.env.NOTE_TEMPLATE_TIME_ZONE || 'Asia/Shanghai';

function assertText(value, label) {
  if (typeof value !== 'string') {
    throw new TypeError(`${label} must be a string`);
  }
  if (Buffer.byteLength(value, 'utf8') > MAX_TEXT_BYTES) {
    throw new Error(`${label} exceeds the 100000-byte limit`);
  }
  if (value.includes('\u0000')) {
    throw new Error(`${label} contains a NUL byte`);
  }
  return value;
}

function timeParts(now, timeZone) {
  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  });
  const parts = Object.fromEntries(formatter.formatToParts(now).map(({ type, value }) => [type, value]));
  const date = `${parts.year}-${parts.month}-${parts.day}`;
  const time = `${parts.hour}:${parts.minute}`;
  return { date, time };
}

/**
 * Render the deliberately small, data-only subset of an Obsidian Templater
 * workflow supported by this example. It never evaluates JavaScript, reads a
 * Vault, accesses files, or makes an outbound request.
 */
export function renderDailyNote(selection, now = new Date(), timeZone = DEFAULT_TIME_ZONE) {
  const selected = assertText(selection, 'selection').trim();
  const { date, time } = timeParts(now, timeZone);
  const focus = selected || '在这里写下今天最重要的事情。';
  return [
    '---',
    `date: ${date}`,
    `created: ${time}`,
    'tags:',
    '  - daily',
    '---',
    '',
    `# ${date}`,
    '',
    '## 今日重点',
    '',
    focus,
    '',
    '## 待办',
    '',
    '- [ ] ',
    '',
    '## 记录',
    '',
  ].join('\n');
}

/**
 * Convert the current selection into unchecked Markdown tasks. Existing list
 * markers and checkbox state are removed so repeated invocation is stable.
 */
export function renderChecklist(selection) {
  const selected = assertText(selection, 'selection').trim();
  const lines = (selected ? selected.split(/\r?\n/) : ['在这里添加待办'])
    .map((line) => line
      .replace(/^\s*(?:[-*+]\s+|\d+[.)]\s+)/, '')
      .replace(/^\s*\[[ xX]\]\s+/, '')
      .trim())
    .filter(Boolean);
  return lines.map((line) => `- [ ] ${line}`).join('\n');
}

export const COMMANDS = [
  {
    id: 'daily-note-template',
    name: '插入每日笔记模板',
    aliases: ['每日模板', '今日笔记', '日记模板', 'daily-note'],
    tool: 'obsidian.note-template.daily',
  },
  {
    id: 'selection-checklist',
    name: '将选区整理为待办',
    aliases: ['整理待办', '待办清单', 'checklist'],
    tool: 'obsidian.note-template.checklist',
  },
];
