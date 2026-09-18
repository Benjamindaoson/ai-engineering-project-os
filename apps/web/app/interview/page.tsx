'use client'

import { useState } from 'react'

// Mock interview data
const mockInterview = {
  session_id: "session-1",
  project_name: "AIEduRAG",
  project_intro: "这是一个教育领域的检索增强生成(RAG)系统，帮助用户从大量教育资料中快速找到相关内容并生成准确答案。",
  questions: [
    {
      id: "q1",
      question: "请介绍一下这个项目，解决了什么问题？",
      context: "Project type: RAG",
      follow_ups: [
        "目标用户是谁？",
        "核心价值主张是什么？",
        "与现有解决方案有什么不同？",
      ],
      status: "pending",
    },
    {
      id: "q2",
      question: "为什么选择混合检索而不是纯向量检索？",
      context: "Architecture decision: hybrid retrieval",
      follow_ups: [
        "纯向量检索有什么问题？",
        "如何确定混合权重？",
        "有哪些trade-off？",
      ],
      status: "pending",
    },
    {
      id: "q3",
      question: "重新排序的Cross-Encoder模型是如何选型的？",
      context: "Implementation: reranking",
      follow_ups: [
        "为什么选择这个模型？",
        "有什么替代方案？",
        "如何评估重排效果？",
      ],
      status: "pending",
    },
  ],
  gap_analysis: [
    {
      gap_type: "knowledge",
      description: "对分布式系统一致性的理解不足",
      severity: "medium",
    },
    {
      gap_type: "evidence",
      description: "缺少A/B测试数据",
      severity: "high",
    },
  ],
}

export default function InterviewPage() {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [followUpIndex, setFollowUpIndex] = useState<Record<string, number>>({})
  const [showAnswer, setShowAnswer] = useState(false)

  const questions = mockInterview.questions
  const currentQ = questions[currentQuestion]

  const handleAnswer = (answer: string) => {
    setAnswers({ ...answers, currentQ.id]: answer })
    setShowAnswer(true)
  }

  const handleNext = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1)
      setShowAnswer(false)
    }
  }

  const handleFollowUp = () => {
    const currentFollowUps = followUpIndex[currentQ.id] || 0
    if (currentFollowUps < currentQ.follow_ups.length) {
      setFollowUpIndex({ ...followUpIndex, [currentQ.id]: currentFollowUps + 1 })
    }
  }

  return (
    <div className="max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">面试工作台</h1>
        <p className="text-gray-600">{mockInterview.project_name} - 基于真实项目的技术面试</p>
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
        {/* Context */}
        <div className="mb-6">
          <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">
            {currentQ.context}
          </span>
        </div>

        {/* Question */}
        <h2 className="text-2xl font-semibold mb-6">
          Q{currentQuestion + 1}: {currentQ.question}
        </h2>

        {/* Answer Input */}
        {!showAnswer ? (
          <div className="space-y-4">
            <textarea
              placeholder="在此输入你的回答..."
              className="w-full h-40 p-4 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
              value={answers[currentQ.id] || ''}
              onChange={(e) => setAnswers({ ...answers, [currentQ.id]: e.target.value })}
            />
            <div className="flex gap-3">
              <button
                onClick={() => handleAnswer(answers[currentQ.id] || '')}
                disabled={!answers[currentQ.id]?.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                提交回答
              </button>
              <button
                onClick={handleNext}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50"
              >
                跳过
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Your Answer */}
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-600 mb-2">你的回答</p>
              <p className="text-gray-800">{answers[currentQ.id]}</p>
            </div>

            {/* Follow-ups */}
            {currentQ.follow_ups.length > 0 && (
              <div className="space-y-4">
                <h3 className="font-medium text-gray-700">追问</h3>
                {(followUpIndex[currentQ.id] || 0) > 0 && (
                  <div className="space-y-3">
                    {currentQ.follow_ups.slice(0, followUpIndex[currentQ.id]).map((followUp: string, i: number) => (
                      <div key={i} className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <p className="text-sm text-yellow-600 mb-1">追问 {i + 1}</p>
                        <p className="font-medium">{followUp}</p>
                        <textarea
                          placeholder="你的回答..."
                          className="w-full mt-3 p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
                          rows={2}
                        />
                      </div>
                    ))}
                  </div>
                )}
                
                {(followUpIndex[currentQ.id] || 0) < currentQ.follow_ups.length && (
                  <button
                    onClick={handleFollowUp}
                    className="px-4 py-2 border border-yellow-400 text-yellow-700 rounded-lg hover:bg-yellow-50"
                  >
                    + 继续追问
                  </button>
                )}
              </div>
            )}

            {/* Next Button */}
            <div className="flex justify-end">
              <button
                onClick={handleNext}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
              >
                {currentQuestion < questions.length - 1 ? '下一题' : '完成面试'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Gap Analysis */}
      {mockInterview.gap_analysis.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-8 mb-8">
          <h2 className="text-xl font-semibold mb-6">发现的缺口</h2>
          <div className="space-y-4">
            {mockInterview.gap_analysis.map((gap, i) => (
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
          {questions.map((q, i) => (
            <button
              key={q.id}
              onClick={() => {
                setCurrentQuestion(i)
                setShowAnswer(false)
              }}
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
