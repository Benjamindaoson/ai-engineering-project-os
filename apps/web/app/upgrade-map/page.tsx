'use client'

import { useState, useEffect, useCallback } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'

export default function UpgradeMapPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const projectId = searchParams.get('project_id')
  
  const [loading, setLoading] = useState(true)
  const [planning, setPlanning] = useState(false)
  const [error, setError] = useState('')
  const [data, setData] = useState<any>(null)

  const fetchPlan = useCallback(async () => {
    if (!projectId) {
      setLoading(false)
      return
    }

    try {
      const response = await fetch(`/api/projects/${projectId}/plan`, {
        method: 'POST',
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to generate plan')
      }
      
      const planData = await response.json()
      setData(planData)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    if (projectId) {
      fetchPlan()
    }
  }, [projectId, fetchPlan])

  const handleGeneratePlan = async () => {
    if (!projectId) return
    
    setPlanning(true)
    setError('')
    
    try {
      const response = await fetch(`/api/projects/${projectId}/plan`, {
        method: 'POST',
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to generate plan')
      }
      
      const planData = await response.json()
      setData(planData)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setPlanning(false)
    }
  }

  if (!projectId) {
    return (
      <div className="max-w-6xl">
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
          <p className="text-yellow-800">请先选择一个项目</p>
          <button
            onClick={() => router.push('/projects/import')}
            className="mt-4 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
          >
            去导入
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
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  const maturityLabels: Record<string, string> = {
    idea: "想法",
    demo: "演示版",
    mvp: "最小可用版本",
    pre_production: "准生产级",
    production: "生产级",
  }

  const levels = ["idea", "demo", "mvp", "pre_production", "production"]
  const currentIndex = levels.indexOf(data?.current_level || 'idea')

  return (
    <div className="max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">升级地图</h1>
        <p className="text-gray-600">从当前阶段到目标的完整升级路线</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {!data ? (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-8 text-center">
          <h2 className="text-xl font-semibold text-blue-800 mb-4">尚未生成升级计划</h2>
          <p className="text-blue-600 mb-6">系统将根据项目体检结果生成个性化升级路线</p>
          <button
            onClick={handleGeneratePlan}
            className="px-8 py-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
          >
            {planning ? '生成中...' : '生成升级计划'}
          </button>
        </div>
      ) : (
        <>
          {/* Current Position */}
          <div className="bg-white rounded-xl shadow-sm p-8 mb-8">
            <div className="flex items-center gap-6 mb-6">
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">📍</span>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-1">当前位置</p>
                <h2 className="text-2xl font-bold">{maturityLabels[data.current_level] || data.current_level}</h2>
                <p className="text-gray-600">目标: {maturityLabels[data.target_level] || data.target_level}</p>
              </div>
            </div>

            {/* Upgrade Path */}
            <div className="flex items-center gap-4 overflow-x-auto py-4">
              {levels.map((level, index) => {
                const isPast = index < currentIndex
                const isCurrent = level === data.current_level
                const isFuture = index > currentIndex

                return (
                  <div key={level} className="flex items-center">
                    <div className={`flex flex-col items-center px-4 py-3 rounded-lg ${
                      isPast ? 'bg-green-100' : isCurrent ? 'bg-blue-100' : 'bg-gray-100'
                    }`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        isPast ? 'bg-green-500 text-white' : isCurrent ? 'bg-blue-500 text-white' : 'bg-gray-400 text-white'
                      }`}>
                        {isPast ? '✓' : index + 1}
                      </div>
                      <span className={`text-sm mt-2 font-medium ${
                        isCurrent ? 'text-blue-600' : isPast ? 'text-green-600' : 'text-gray-500'
                      }`}>
                        {maturityLabels[level]}
                      </span>
                    </div>
                    {index < levels.length - 1 && (
                      <div className={`w-12 h-1 mx-2 ${
                        isPast ? 'bg-green-400' : 'bg-gray-200'
                      }`} />
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Recommended Tasks */}
          {data.recommended_tasks?.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm p-8 mb-8">
              <h2 className="text-xl font-semibold mb-6">推荐升级任务 ({data.recommended_tasks.length})</h2>
              
              <div className="space-y-4">
                {data.recommended_tasks.map((task: any, index: number) => (
                  <div key={task.id} className="p-6 border rounded-xl hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                          task.priority === 'critical' ? 'bg-red-100 text-red-600' :
                          task.priority === 'high' ? 'bg-orange-100 text-orange-600' :
                          task.priority === 'medium' ? 'bg-yellow-100 text-yellow-600' : 'bg-gray-100 text-gray-600'
                        }`}>
                          {index + 1}
                        </div>
                        <div>
                          <h3 className="font-semibold text-lg">{task.title}</h3>
                          <p className="text-gray-600">{task.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`px-3 py-1 rounded-full text-sm ${
                          task.priority === 'critical' ? 'bg-red-100 text-red-700' :
                          task.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {task.priority === 'critical' ? '关键' : task.priority === 'high' ? '高' : '中'}优先级
                        </span>
                        <span className="px-3 py-1 bg-gray-100 rounded-full text-sm text-gray-600">
                          {task.estimated_effort || task.effort}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-gray-500">维度: {task.dimension}</span>
                      <a
                        href={`/tasks?task_id=${task.id}&project_id=${projectId}`}
                        className="ml-auto px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                      >
                        开始任务
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Rationale */}
          {data.prioritization_rationale && (
            <div className="bg-gray-50 rounded-xl p-8 mb-8">
              <h2 className="text-xl font-semibold mb-4">优先级说明</h2>
              <p className="text-gray-700">{data.prioritization_rationale}</p>
            </div>
          )}

          {/* Immediate Steps */}
          {data.immediate_next_steps?.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm p-8">
              <h2 className="text-xl font-semibold mb-6">立即行动</h2>
              <ol className="space-y-4">
                {data.immediate_next_steps.map((step: string, index: number) => (
                  <li key={index} className="flex items-start gap-4">
                    <span className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                      {index + 1}
                    </span>
                    <span className="pt-1">{step}</span>
                  </li>
                ))}
              </ol>
              
              {data.estimated_total_effort && (
                <div className="mt-6 pt-6 border-t">
                  <p className="text-gray-600">
                    预计总工作量: <span className="font-semibold text-gray-900">{data.estimated_total_effort}</span>
                  </p>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
