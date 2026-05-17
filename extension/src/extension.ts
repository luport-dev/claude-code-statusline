import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

interface PluginSession {
  sessionId: string;
  title: string;
  state: 'idle' | 'running' | string;
  lastUpdate: number;
}

interface PluginState {
  sessions: Map<string, PluginSession>;
  model?: string;
  effortLevel?: string;
  thinking?: boolean;
  contextWindow?: number;
}

const HOME = os.homedir();
const VSCODE_LOG_BASE = path.join(HOME, '.config', 'Code', 'logs');

function findLatestPluginLog(): string | undefined {
  if (!fs.existsSync(VSCODE_LOG_BASE)) return undefined;
  const sessions = fs
    .readdirSync(VSCODE_LOG_BASE)
    .filter((d) => /^\d{8}T\d{6}$/.test(d))
    .sort()
    .reverse();
  for (const session of sessions) {
    const sessionDir = path.join(VSCODE_LOG_BASE, session);
    // Search window subdirs
    let windows: string[] = [];
    try {
      windows = fs.readdirSync(sessionDir).filter((d) => d.startsWith('window'));
    } catch {
      continue;
    }
    for (const win of windows) {
      const logPath = path.join(
        sessionDir,
        win,
        'exthost',
        'Anthropic.claude-code',
        'Claude VSCode.log'
      );
      if (fs.existsSync(logPath)) {
        // Check it was modified recently (in last hour)
        const stat = fs.statSync(logPath);
        if (Date.now() - stat.mtimeMs < 60 * 60 * 1000) {
          return logPath;
        }
      }
    }
  }
  return undefined;
}

function parsePluginLog(logPath: string): PluginState {
  const state: PluginState = { sessions: new Map() };

  // Read tail of file (last 256KB should be plenty for current state)
  const stats = fs.statSync(logPath);
  const readSize = Math.min(stats.size, 512 * 1024);
  const buf = Buffer.alloc(readSize);
  const fd = fs.openSync(logPath, 'r');
  fs.readSync(fd, buf, 0, readSize, Math.max(0, stats.size - readSize));
  fs.closeSync(fd);
  const text = buf.toString('utf8');
  const lines = text.split('\n');

  for (const line of lines) {
    // session_state updates: {"type":"update_session_state","sessionId":"...","state":"idle","title":"..."}
    const sessionMatch = line.match(
      /"type":"update_session_state","sessionId":"([^"]+)","state":"([^"]+)","title":"([^"]*)"/
    );
    if (sessionMatch) {
      const [, sessionId, sessState, title] = sessionMatch;
      const tsMatch = line.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)/);
      const ts = tsMatch ? new Date(tsMatch[1]).getTime() : Date.now();
      state.sessions.set(sessionId, { sessionId, title, state: sessState, lastUpdate: ts });
      continue;
    }

    // effort: {"settings":{"effortLevel":"medium"}}
    const effortMatch = line.match(/"effortLevel":"([^"]+)"/);
    if (effortMatch) state.effortLevel = effortMatch[1];

    // thinking
    const thinkingMatch = line.match(/"thinking":\s*(true|false)/);
    if (thinkingMatch) state.thinking = thinkingMatch[1] === 'true';

    // model — primary source: user-issued set_model events from the webview.
    // Format: {"type":"set_model","model":{"value":"opus", ...}}
    // value can be: "opus" | "sonnet" | "haiku" | "default" (= Opus).
    const setModelMatch = line.match(/"type":"set_model","model":\{"value":"([^"]+)"/);
    if (setModelMatch) {
      const v = setModelMatch[1];
      if (v === 'default') state.model = 'claude-opus-4-7';
      else if (v === 'opus' || v === 'sonnet' || v === 'haiku') state.model = `claude-${v}`;
      else state.model = v;
    } else if (state.model === undefined) {
      // Fallback: scrape debug lines for a claude-* identifier so we have *something*
      // before the user has switched models in this session.
      const modelMatch = line.match(/claude-(opus|sonnet|haiku)-[\w-]+/);
      if (modelMatch) state.model = modelMatch[0];
    }

    // context window: effectiveWindow=180000
    const ctxMatch = line.match(/effectiveWindow=(\d+)/);
    if (ctxMatch) state.contextWindow = parseInt(ctxMatch[1], 10);
  }

  return state;
}

function formatModel(model?: string): string {
  if (!model) return '?';
  if (model.includes('opus')) return 'Opus';
  if (model.includes('sonnet')) return 'Sonnet';
  if (model.includes('haiku')) return 'Haiku';
  return model;
}

function stateIcon(s: string): string {
  if (s === 'running' || s === 'busy') return '$(sync~spin)';
  if (s === 'idle') return '$(check)';
  return '$(circle-outline)';
}

export function activate(context: vscode.ExtensionContext) {
  const statusBarItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    100
  );
  statusBarItem.command = 'claudeStatusLine.selectSession';
  statusBarItem.show();
  context.subscriptions.push(statusBarItem);

  let selectedSessionId: string | undefined;
  let logPath: string | undefined;

  function update() {
    if (!logPath || !fs.existsSync(logPath)) {
      logPath = findLatestPluginLog();
    }
    if (!logPath) {
      statusBarItem.text = '$(circle-slash) Claude: no plugin log';
      return;
    }

    const state = parsePluginLog(logPath);
    if (state.sessions.size === 0) {
      statusBarItem.text = `${state.model ? formatModel(state.model) : '$(circle-slash) Claude'}: no session`;
      return;
    }

    const all = [...state.sessions.values()].sort((a, b) => b.lastUpdate - a.lastUpdate);
    const active = all.find((s) => s.sessionId === selectedSessionId) ?? all[0];

    const sep = ' | ';
    const parts: string[] = [
      `${stateIcon(active.state)} ${formatModel(state.model)}`,
      `eff:${state.effortLevel ?? '--'}`,
      `think:${state.thinking === undefined ? '--' : state.thinking ? 'on' : 'off'}`,
      `ctx:--`,
      `5h:--`,
      `7d:--`,
    ];
    statusBarItem.text = parts.join(sep);
    statusBarItem.tooltip = new vscode.MarkdownString(
      `**Claude VS Code Plugin**\n\n` +
        `- Session: \`${active.sessionId}\`\n` +
        `- State: ${active.state}\n` +
        `- Title: ${active.title}\n` +
        `- Model: ${state.model ?? 'unknown'}\n` +
        `- Effort: ${state.effortLevel ?? 'unknown'}\n` +
        `- Thinking: ${state.thinking ?? 'unknown'}\n` +
        `- Context window: ${state.contextWindow ?? 'unknown'}\n` +
        `- Sessions tracked: ${all.length}\n\n` +
        `Click to switch session.`
    );
  }

  const selectCmd = vscode.commands.registerCommand(
    'claudeStatusLine.selectSession',
    async () => {
      if (!logPath) return;
      const state = parsePluginLog(logPath);
      const all = [...state.sessions.values()].sort((a, b) => b.lastUpdate - a.lastUpdate);
      if (all.length === 0) {
        vscode.window.showInformationMessage('No Claude sessions in plugin log');
        return;
      }
      const choice = await vscode.window.showQuickPick(
        all.map((s) => ({
          label: s.title || s.sessionId.slice(0, 8),
          description: `${s.state} · ${new Date(s.lastUpdate).toLocaleTimeString()}`,
          detail: s.sessionId,
          id: s.sessionId,
        })),
        { placeHolder: 'Select Claude plugin session' }
      );
      if (choice) {
        selectedSessionId = choice.id;
        update();
      }
    }
  );
  context.subscriptions.push(selectCmd);

  const interval = setInterval(update, 1500);
  context.subscriptions.push({ dispose: () => clearInterval(interval) });

  update();
}

export function deactivate() {}
