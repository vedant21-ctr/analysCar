import React, { useState, useRef, useEffect } from 'react';
import { useApi } from '../hooks/useApi';
import './AIAssistant.css';

const CATEGORY_ICONS = {
  demand: '📈',
  weather: '🌧️',
  revenue: '💰',
  drivers: '🚗',
  cancellations: '❌',
  sustainability: '🌍',
};

const CATEGORY_COLORS = {
  demand: '#4f8ef7',
  weather: '#06b6d4',
  revenue: '#10b981',
  drivers: '#f59e0b',
  cancellations: '#ef4444',
  sustainability: '#10b981',
};

const QUICK_QUESTIONS = [
  "What are the peak demand hours?",
  "How does rain affect cancellations?",
  "Which zones have the best driver earnings?",
  "What's the surge pricing strategy?",
  "How can we reduce CO₂ emissions?",
  "What are the cancellation hotspots?",
];

export default function AIAssistant() {
  const { data: insights, loading } = useApi('/api/insights');
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "👋 Hello! I'm the Urban Mobility AI Assistant. I've analyzed 50,000+ rides across your city. Ask me anything about demand patterns, driver strategy, revenue optimization, or sustainability.",
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [activeCategory, setActiveCategory] = useState('demand');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const findRelevantInsight = (question) => {
    if (!insights) return null;
    const q = question.toLowerCase();

    if (q.includes('demand') || q.includes('peak') || q.includes('hour') || q.includes('busy'))
      return insights.demand?.[Math.floor(Math.random() * insights.demand.length)];
    if (q.includes('rain') || q.includes('weather') || q.includes('snow') || q.includes('fog'))
      return insights.weather?.[Math.floor(Math.random() * insights.weather.length)];
    if (q.includes('revenue') || q.includes('money') || q.includes('earn') || q.includes('fare'))
      return insights.revenue?.[Math.floor(Math.random() * insights.revenue.length)];
    if (q.includes('driver') || q.includes('zone') || q.includes('best'))
      return insights.drivers?.[Math.floor(Math.random() * insights.drivers.length)];
    if (q.includes('cancel') || q.includes('wait'))
      return insights.cancellations?.[Math.floor(Math.random() * insights.cancellations.length)];
    if (q.includes('co2') || q.includes('emission') || q.includes('eco') || q.includes('green') || q.includes('sustain'))
      return insights.sustainability?.[Math.floor(Math.random() * insights.sustainability.length)];

    // Random insight
    const allInsights = Object.values(insights).flat();
    return allInsights[Math.floor(Math.random() * allInsights.length)];
  };

  const sendMessage = async (text) => {
    const userMsg = text || input.trim();
    if (!userMsg) return;

    setMessages(prev => [...prev, {
      role: 'user',
      content: userMsg,
      timestamp: new Date(),
    }]);
    setInput('');
    setTyping(true);

    // Simulate AI thinking
    await new Promise(r => setTimeout(r, 800 + Math.random() * 600));

    const insight = findRelevantInsight(userMsg);
    const response = insight
      ? `${insight}\n\n*Based on analysis of 50,000+ rides across 20 city zones.*`
      : "I'm analyzing the data... Based on current patterns, I recommend checking the Decision Engine for detailed zone-specific recommendations. The simulation panel can also help you model different scenarios.";

    setMessages(prev => [...prev, {
      role: 'assistant',
      content: response,
      timestamp: new Date(),
    }]);
    setTyping(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title gradient-text-blue">AI Insight Assistant</h1>
        <p className="page-subtitle">Natural language interface to your mobility intelligence platform</p>
      </div>

      <div className="ai-layout">
        {/* Insights Panel */}
        <div className="insights-panel">
          <div className="insights-header">
            <span>🧠 Live Insights</span>
            <div className="insights-tabs">
              {Object.keys(CATEGORY_ICONS).map(cat => (
                <button
                  key={cat}
                  className={`insight-tab ${activeCategory === cat ? 'active' : ''}`}
                  onClick={() => setActiveCategory(cat)}
                  style={{ '--cat-color': CATEGORY_COLORS[cat] }}
                >
                  {CATEGORY_ICONS[cat]}
                </button>
              ))}
            </div>
          </div>

          <div className="insights-body">
            {loading ? (
              <div className="insights-loading">
                <div className="insights-spinner" />
                <p>Generating insights...</p>
              </div>
            ) : (
              <>
                <div className="insights-category-label">
                  {CATEGORY_ICONS[activeCategory]} {activeCategory.charAt(0).toUpperCase() + activeCategory.slice(1)} Insights
                </div>
                {(insights?.[activeCategory] || []).map((insight, i) => (
                  <div
                    key={i}
                    className="insight-card"
                    style={{ '--insight-color': CATEGORY_COLORS[activeCategory] }}
                    onClick={() => sendMessage(`Tell me more: ${insight.substring(0, 60)}...`)}
                  >
                    <p className="insight-text">{insight}</p>
                    <span className="insight-ask">Ask AI →</span>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>

        {/* Chat Panel */}
        <div className="chat-panel">
          {/* Messages */}
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                {msg.role === 'assistant' && (
                  <div className="message-avatar">🤖</div>
                )}
                <div className="message-bubble">
                  <p className="message-content">{msg.content}</p>
                  <span className="message-time">
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                {msg.role === 'user' && (
                  <div className="message-avatar user-avatar">👤</div>
                )}
              </div>
            ))}

            {typing && (
              <div className="message assistant">
                <div className="message-avatar">🤖</div>
                <div className="message-bubble typing-bubble">
                  <div className="typing-dots">
                    <span /><span /><span />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick questions */}
          <div className="quick-questions">
            {QUICK_QUESTIONS.map((q, i) => (
              <button key={i} className="quick-btn" onClick={() => sendMessage(q)}>
                {q}
              </button>
            ))}
          </div>

          {/* Input */}
          <div className="chat-input-area">
            <textarea
              className="chat-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about demand patterns, driver strategy, revenue optimization..."
              rows={2}
            />
            <button
              className="send-btn"
              onClick={() => sendMessage()}
              disabled={!input.trim() || typing}
            >
              <span>↑</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
