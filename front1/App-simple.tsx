import { useState } from 'react';
import { marked } from 'marked';

const API_BASE = '';

interface StatusEvent {
  node: string;
  status: string;
}

export default function App() {
  const [input, setInput] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusNodes, setStatusNodes] = useState<string[]>([]);

  const quickActions = [
    '帮我分析"租房避坑"的选题',
    '写一个手机评测口播脚本',
    '把这段文案改成小红书版',
    '帮我校审这段短视频文案',
  ];

  const handleSend = async (text?: string) => {
    const msg = text || input;
    if (!msg.trim() || loading) return;

    setLoading(true);
    setOutput('');
    setStatusNodes([]);

    try {
      const res = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, session_id: `ui-${Date.now()}` }),
      });

      const reader = res.body?.getReader();
      if (!reader) return;

      const decoder = new TextDecoder();
      let buffer = '';
      let currentEvent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith('data:')) {
            const raw = line.slice(5).trim();
            if (currentEvent === 'chunk') {
              setOutput(prev => prev + raw);
            } else if (currentEvent === 'done') {
              try {
                const doneData = JSON.parse(raw);
                if (doneData.answer) {
                  setOutput(doneData.answer);
                }
              } catch {}
            } else if (currentEvent === 'status') {
              try {
                const s = JSON.parse(raw) as StatusEvent;
                setStatusNodes(prev => [...new Set([...prev, s.node])]);
              } catch {}
            }
          }
        }
      }
    } catch (e) {
      setOutput(`错误: ${e}`);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div>
      <header className="creator-header">
        <h1>CreatorOS</h1>
        <p>AI 多智能体内容创作工作台 · 选题 · 脚本 · 改编 · 审核</p>
      </header>

      <div className="creator-input-area">
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入你的创作需求，例如：我要做一期关于'租房避坑'的短视频..."
          disabled={loading}
        />
        <button onClick={() => handleSend()} disabled={loading}>
          {loading ? '创作者 Agents 工作中...' : '🚀 开始创作'}
        </button>
        <div className="quick-actions">
          {quickActions.map(action => (
            <button key={action} onClick={() => { setInput(action); handleSend(action); }}>
              {action}
            </button>
          ))}
        </div>
      </div>

      {loading && statusNodes.length > 0 && (
        <div className="agent-status-bar">
          {statusNodes.map(node => (
            <span key={node} className="agent-status-tag active">{node}</span>
          ))}
        </div>
      )}

      {output ? (
        <div className="creator-output" dangerouslySetInnerHTML={{ __html: marked.parse(output) }} />
      ) : !loading ? (
        <div className="creator-empty">
          <div className="icon">✨</div>
          <p>输入你的创作需求，让 AI 多智能体为你工作</p>
        </div>
      ) : null}
    </div>
  );
}
