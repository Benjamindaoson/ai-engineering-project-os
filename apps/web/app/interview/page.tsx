'use client'

import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'next/navigation'

export default function InterviewPage() {
  const searchParams = useSearchParams()
  const projectId = searchParams.get('project_id')
  
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState('')
  const [session, setSession] = useState<any>(null)
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})

  const fetchInterview = useCallback(async () => {
    if (!projectId) {
      setLoading(false)
      return
    }

    try {
      const response = await fetch(`/api/projects/${projectId}/interview`, {
        method: 'POST',
      })
      
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to start interview')
      }
      
      const data = await response.json()
      setSession(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    fetchInterview()
  }, [fetchInterview])

  const handleStartNew = async () => {
    setStarting(true)
    await fetchInterview()
    setStarting(false)
  }

  if (!projectId) {
    return (
      <div className="max-w-6xl">
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
          <p className="text-yellow-800">请先选择一个项目</p>
        </div>
      </div>
    )
  }

  if (loading || starting) {
    return (
      <div className="max-w-4xl">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    )
  }

  if (error && !session) {
    return (
      <div className="max-w-4xl">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <p className="text-red-700 mb-4">{error}</p>
          <button
            onClick={handleStartNew}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            重试
          </button>
        </div>
      </div>
    )
  }

  if (!session || !session.questions?.length) {
    return (
      <div className="max-w-4xl">
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-8 text-center">
          <h2 className="text-xl font-semibold text-blue-800 mb-4">面试会话</h2>
          <p className="text-blue-600 mb-6">系统将基于项目实际情况生成面试问题</p>
          <button
            onClick={handleStartNew}
            className="px-8 py-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
          >
            开始面试
          </button>
        </div>
      </div>
    )
  }

  const questions = session.questions
  const currentQ = questions[currentQuestion]

  return (
    <div className="max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">面试工作台</h1>
        <p className="text-gray-600">基于真实项目的技术面试</p>
      </div>

      {/* Progress */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm text-gray-500">问题进度</span>
          <span className="text-sm font-medium">{currentQuestion + 1} / {questions.length}</span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div 
            className="h-full bg-blue-600 transition-all duration-300"
            style={{ width: `${((currentQuestion + 1) / questions.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Current Question */}
      <div className="bg-white rounded-xl shadow-sm p-8 mb-8">
        {currentQ && (
          <>
            {/* Context */}
            {currentQ.context && (
              <div className="mb-6">
                <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">
                  {currentQ.context}
                </span>
              </div>
            )}

            {/* Question */}
            <h2 className="text-2xl font-semibold mb-6">
              Q{currentQuestion + 1}: {currentQ.question}
            </h2>

            {/* Answer Input */}
            {answers[currentQ.id] !== undefined ? (
              <div className="space-y-4">
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-600 mb-2">你的回答</p>
                  <p className="text-gray-800">{answers[currentQ.id]}</p>
                </div>

                {/* Next Button */}
                <div className="flex justify-end">
                  <button
                    onClick={() => setCurrentQuestion(Math.min(currentQuestion + 1, questions.length - 1))}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
                  >
                    {currentQuestion < questions.length - 1 ? '下一题' : '完成面试'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <textarea
                  placeholder="在此输入你的回答..."
                  className="w-full h-40 p-4 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
                  value={answers[currentQ.id] || ''}
                  onChange={(e) => setAnswers({ ...answers, [currentQ.id]: e.target.value })}
                />
                <div className="flex gap-3">
                  <button
                    onClick={() => setAnswers({ ...answers, [currentQ.id]: answers[currentQ.id] || '' })}
                    disabled={!answers[currentQ.id]?.trim()}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    提交回答
                  </button>
                  <button
                    onClick={() => setCurrentQuestion(Math.min(currentQuestion + 1, questions.length - 1))}
                    className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50"
                  >
                    跳过
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Gap Analysis */}
      {session.gap_analysis?.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-8 mb-8">
          <h2 className="text-xl font-semibold mb-6">发现的缺口</h2>
          <div className="space-y-4">
            {session.gap_analysis.map((gap: any, i: number) => (
              <div key={i} className={`p-4 rounded-lg border ${
                gap.severity === 'high' ? 'bg-red-50 border-red-200' :
                gap.severity === 'medium' ? 'bg-yellow-50 border-yellow-200' :
                'bg-gray-50 border-gray-200'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    gap.gap_type === 'knowledge' ? 'bg-purple-100 text-purple-700' :
                    gap.gap_type === 'evidence' ? 'bg-blue-100 text-blue-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {gap.gap_type === 'knowledge' ? '知识缺口' :
                     gap.gap_type === 'evidence' ? '证据缺口' : '工程缺口'}
                  </span>
                  <span className={`text-sm ${
                    gap.severity === 'high' ? 'text-red-600' :
                    gap.severity === 'medium' ? 'text-yellow-600' : 'text-gray-600'
                  }`}>
                    {gap.severity === 'high' ? '高' : gap.severity === 'medium' ? '中' : '低'}优先级
                  </span>
                </div>
                <p className="text-gray-700">{gap.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Question List */}
      <div className="bg-white rounded-xl shadow-sm p-8">
        <h2 className="text-xl font-semibold mb-6">问题列表</h2>
        <div className="space-y-3">
          {questions.map((q: any, i: number) => (
            <button
              key={q.id}
              onClick={() => setCurrentQuestion(i)}
              className={`w-full p-4 rounded-lg border text-left transition-colors ${
                i === currentQuestion ? 'border-blue-300 bg-blue-50' : 'hover:border-gray-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium">
                  Q{i + 1}: {q.question}
                </span>
                <span className={`w-3 h-3 rounded-full ${
                  answers[q.id] ? 'bg-green-500' : 'bg-gray-300'
                }`} />
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
