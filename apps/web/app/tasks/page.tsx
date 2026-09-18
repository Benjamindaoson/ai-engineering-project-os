'use client'

import { useState, useEffect, useCallback } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'

export default function TasksPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const taskId = searchParams.get('task_id')
  const projectId = searchParams.get('project_id')
  
  const [loading, setLoading] = useState(true)
  const [executing, setExecuting] = useState(false)
  const [error, setError] = useState('')
  const [task, setTask] = useState<any>(null)
  const [executionResult, setExecutionResult] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<'details' | 'mentor' | 'execute'>('details')

  const fetchTask = useCallback(async () => {
    if (!taskId) {
      setLoading(false)
      return
    }

    try {
      const response = await fetch(`/api/tasks/${taskId}`)
      if (!response.ok) throw new Error('Task not found')
      const data = await response.json()
      setTask(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [taskId])

  useEffect(() => {
    fetchTask()
  }, [fetchTask])

  const handleExecute = async () => {
    if (!taskId) return
    
    setExecuting(true)
    setError('')
    
    try {
      const response = await fetch(`/api/tasks/${taskId}/execute`, {
        method: 'POST',
      })
      
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Execution failed')
      }
      
      const result = await response.json()
      setExecutionResult(result)
      
      // Refresh task to get updated status
      await fetchTask()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setExecuting(false)
    }
  }

  if (!taskId) {
    return (
      <div className="max-w-6xl">
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
          <p className="text-yellow-800">请先选择一个任务</p>
          <button
            onClick={() => router.push(projectId ? `/upgrade-map?project_id=${projectId}` : '/projects/import')}
            className="mt-4 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
          >
            去选择
          </button>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="max-w-6xl">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-8"></div>
        </div>
      </div>
    )
  }

  if (error && !task) {
    return (
      <div className="max-w-6xl">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <p className="text-red-700">{error}</p>
        </div>
      </div>
    )
  }

  const statusLabels: Record<string, string> = {
    pending: '待开始',
    in_progress: '进行中',
    completed: '已完成',
    failed: '失败',
  }

  return (
    <div className="max-w-6xl">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
          <a href={projectId ? `/upgrade-map?project_id=${projectId}` : '/projects/import'} className="hover:text-blue-600">
            升级地图
          </a>
          <span>/</span>
          <span>工程任务</span>
        </div>
        <h1 className="text-3xl font-bold mb-2">{task?.title}</h1>
        <p className="text-gray-600">{task?.description}</p>
      </div>

      {/* Status Bar */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <StatusItem label="维度" value={task?.dimension || 'N/A'} />
            <StatusItem label="优先级" value={task?.priority || 'N/A'} />
            <StatusItem label="预计工时" value={task?.estimated_effort || 'N/A'} />
            <StatusItem label="状态" value={statusLabels[task?.status] || task?.status} />
          </div>
          
          {task?.status === 'pending' && (
            <button
              onClick={handleExecute}
              disabled={executing}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
            >
              {executing ? '执行中...' : '开始执行'}
            </button>
          )}
          
          {executionResult && (
            <a
              href={`/evidence?project_id=${task?.project_id}`}
              className="px-6 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700"
            >
              查看证据
            </a>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Execution Result */}
      {executionResult && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-6 mb-8">
          <h3 className="font-semibold text-green-800 mb-4">
            {executionResult.status === 'completed' ? '执行完成' : '执行失败'}
          </h3>
          <div className="space-y-2">
            <p>状态: <span className="font-medium">{statusLabels[executionResult.status]}</span></p>
            <p>文件变更: {executionResult.changes} 个</p>
            <p>测试结果: {executionResult.test_results} 个</p>
            {executionResult.error && (
              <p className="text-red-600">错误: {executionResult.error}</p>
            )}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="border-b">
          <nav className="flex">
            <TabButton active={activeTab === 'details'} onClick={() => setActiveTab('details')}>
              任务详情
            </TabButton>
            <TabButton active={activeTab === 'mentor'} onClick={() => setActiveTab('mentor')}>
              工程导师
            </TabButton>
            <TabButton active={activeTab === 'execute'} onClick={() => setActiveTab('execute')}>
              执行记录
            </TabButton>
          </nav>
        </div>

        <div className="p-8">
          {activeTab === 'details' && (
            <div className="space-y-6">
              <div>
                <h3 className="font-semibold mb-3">完成标准</h3>
                <div className="space-y-3">
                  {(task?.completion_criteria || []).map((criterion: any, i: number) => (
                    <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                      <div className="w-6 h-6 border-2 border-gray-300 rounded-full" />
                      <div>
                        <p className="font-medium">{criterion.criterion}</p>
                        <p className="text-sm text-gray-500">验证方式: {criterion.verification_method}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'mentor' && (
            <MentorView taskId={taskId} />
          )}

          {activeTab === 'execute' && (
            <div className="text-center py-12 text-gray-500">
              {executionResult ? (
                <div className="text-left">
                  <h3 className="font-semibold mb-4">执行记录</h3>
                  <pre className="bg-gray-100 p-4 rounded-lg text-sm overflow-auto">
                    {JSON.stringify(executionResult, null, 2)}
                  </pre>
                </div>
              ) : (
                <p>暂无执行记录</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function MentorView({ taskId }: { taskId: string }) {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    const fetchMentor = async () => {
      try {
        const response = await fetch(`/api/tasks/${taskId}/mentor`, {
          method: 'POST',
        })
        if (response.ok) {
          const result = await response.json()
          setData(result)
        }
      } catch (err) {
        console.error('Failed to fetch mentor:', err)
      } finally {
        setLoading(false)
      }
    }
    
    fetchMentor()
  }, [taskId])

  if (loading) {
    return <div className="text-gray-500">加载中...</div>
  }

  if (!data) {
    return <div className="text-gray-500">暂无导师内容</div>
  }

  const learning = data.learning_content || {}

  return (
    <div className="space-y-6">
      <LearningSection title="问题是什么" content={learning.problem_explanation} />
      <LearningSection title="为什么重要" content={learning.why_important} />
      <LearningSection title="最简单的方案" content={learning.simple_solution} />
      <LearningSection title="为什么简单方案不够" content={learning.why_simple_not_enough} />
      <LearningSection title="生产环境通常怎么做" content={learning.production_approach} />
      <LearningSection title="推荐方案" content={learning.recommended_solution} />
      <LearningSection title="如何验证" content={learning.verification_method} />
      
      {data.related_concepts?.length > 0 && (
        <div className="border-t pt-6">
          <h3 className="font-semibold mb-4">相关概念</h3>
          <div className="space-y-3">
            {data.related_concepts.map((concept: any, i: number) => (
              <div key={i} className="p-4 bg-blue-50 rounded-lg">
                <p className="font-medium text-blue-800">{concept.concept}</p>
                <p className="text-sm text-blue-600 mt-1">{concept.explanation}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {data.interview_questions?.length > 0 && (
        <div className="border-t pt-6">
          <h3 className="font-semibold mb-4">面试预览</h3>
          <div className="space-y-3">
            {data.interview_questions.map((q: string, i: number) => (
              <div key={i} className="p-4 bg-purple-50 rounded-lg">
                <p className="font-medium text-purple-800">Q{i + 1}: {q}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function LearningSection({ title, content }: { title: string; content?: string }) {
  if (!content) return null
  
  return (
    <div className="border-b pb-4">
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-gray-700">{content}</p>
    </div>
  )
}

function StatusItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  )
}

function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`px-6 py-4 font-medium border-b-2 transition-colors ${
        active ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
      }`}
    >
      {children}
    </button>
  )
}
