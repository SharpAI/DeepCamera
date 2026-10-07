'use client'
import { useState, useRef, useEffect } from 'react'
import { api } from '@/lib/api'
import { Send, Bot, User, Loader2 } from 'lucide-react'
import { fmtTime } from '@/lib/utils'

interface Message {
  role: 'user' | 'assistant'
  content: string
  time: string
  context?: number
}

const SUGGESTIONS = [
  'How many incidents occurred in the last 24 hours?',
  'List all critical incidents today',
  'Which camera has the most incidents?',
  'Summarize traffic accidents from this week',
]

export default function AgentPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send(question: string) {
    if (!question.trim() || loading) return
    const userMsg: Message = { role: 'user', content: question, time: new Date().toISOString() }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await api.agent.query(question)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.answer,
          time: new Date().toISOString(),
          context: res.incidents_in_context,
        },
      ])
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Failed to get a response. Is the backend running?', time: new Date().toISOString() },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full max-w-3xl mx-auto">
      <h1 className="text-xl font-semibold text-white mb-4">AI Agent</h1>

      {/* Chat window */}
      <div className="flex-1 bg-gray-900 rounded-xl border border-gray-800 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
          {messages.length === 0 && (
            <div className="text-center pt-8">
              <Bot size={40} className="mx-auto text-brand-500 mb-3" />
              <p className="text-gray-400 text-sm mb-6">Ask anything about incidents, cameras, or traffic patterns.</p>
              <div className="grid grid-cols-2 gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="text-left text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-2 rounded-lg transition-colors"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'assistant' && (
                <div className="w-7 h-7 rounded-full bg-brand-600 flex items-center justify-center flex-shrink-0 mt-1">
                  <Bot size={14} />
                </div>
              )}
              <div className={`max-w-lg ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
                <div className={`px-4 py-2.5 rounded-2xl text-sm whitespace-pre-wrap ${
                  msg.role === 'user'
                    ? 'bg-brand-600 text-white rounded-br-sm'
                    : 'bg-gray-800 text-gray-200 rounded-bl-sm'
                }`}>
                  {msg.content}
                </div>
                <span className="text-xs text-gray-600">
                  {fmtTime(msg.time)}
                  {msg.context != null && ` · ${msg.context} incidents in context`}
                </span>
              </div>
              {msg.role === 'user' && (
                <div className="w-7 h-7 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0 mt-1">
                  <User size={14} />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded-full bg-brand-600 flex items-center justify-center">
                <Bot size={14} />
              </div>
              <div className="bg-gray-800 rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-2">
                <Loader2 size={14} className="animate-spin text-brand-400" />
                <span className="text-gray-400 text-sm">Thinking…</span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div className="border-t border-gray-800 p-3 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && send(input)}
            placeholder="Ask about incidents, cameras, or traffic…"
            className="flex-1 bg-gray-800 text-white text-sm rounded-lg px-4 py-2.5 outline-none placeholder-gray-600 focus:ring-1 focus:ring-brand-500"
          />
          <button
            onClick={() => send(input)}
            disabled={loading || !input.trim()}
            className="bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white px-4 py-2.5 rounded-lg transition-colors"
          >
            <Send size={15} />
          </button>
        </div>
      </div>
    </div>
  )
}
