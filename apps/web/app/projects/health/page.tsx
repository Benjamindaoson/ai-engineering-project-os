'use client'

import { useState, useEffect, useCallback } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'

export default function HealthPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const projectId = searchParams.get('project_id')
  
  const [loading, setLoading] = useState(true)
  const [auditing, setAuditing] = useState(false)
  const [error, setError] = useState('')
  const [data, setData] = useState<any>(null)

  const fetchAudit = useCallback(async () => {
    if (!projectId) {
      setLoading(false)
      return
    }

    try {
      const response = await fetch(`/api/projects/${projectId}`)
      if (!response.ok) throw new Error('Project not found')
      const project = await response.json()
      
      // Fetch latest audit
      const auditResponse = await fetch(`/api/projects/${projectId}/audit`)
      if (auditResponse.ok) {
        const auditData = await auditResponse.json()
        setData({
          project,
          ...auditData,
        })
      } else {
        // No audit yet, set project data
        setData({ project })
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    fetchAudit()
  }, [fetchAudit])

  const handleAudit = async () => {
    if (!projectId) return
    
    setAuditing(true)
    setError('')
    
    try {
      const response = await fetch(`/api/projects/${projectId}/audit`, {
        method: 'POST',
      })
      
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Audit failed')
      }
      
      const auditData = await response.json()
      setData((prev: any) => ({
        ...prev,
        ...auditData,
      }))
    } catch (err: any) {
      setError(err.message)
    } finally {
      setAuditing(false)
    }
  }

  if (!projectId) {
    return (
      <div className="max-w-6xl">
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
          <p className="text-yellow-800">请先导入项目</p>
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

  if (error && !data) {
    return (
      <div className="max-w-6xl">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <p className="text-red-700">{error}</p>
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

  const levelColors: Record<string, string> = {
    idea: "bg-gray-400",
    demo: "bg-yellow-400",
    mvp: "bg-blue-400",
    pre_production: "bg-purple-400",
    production: "bg-green-400",
  }

  const currentMaturity = data?.maturity_assessment?.overall_level || data?.project?.current_maturity || 'idea'
  const dimensionScores = data?.maturity_assessment?.dimension_scores || {}
  const gaps = data?.gaps || []
  const projectFacts = data?.project_facts || {}

  return (
    <div className="max-w-6xl">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">项目体检</h1>
          <p className="text-gray-600">
            {data?.project?.name || '项目'} - 全面分析项目现状
          </p>
        </div>
        <button
          onClick={handleAudit}
          disabled={auditing}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300"
        >
          {auditing ? '体检中...' : '重新体检'}
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {!data?.maturity_assessment ? (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-8 text-center">
          <h2 className="text-xl font-semibold text-blue-800 mb-4">项目尚未体检</h2>
          <p className="text-blue-600 mb-6">点击上方「体检」按钮开始分析项目</p>
          <button
            onClick={handleAudit}
            className="px-8 py-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
          >
            开始体检
          </button>
        </div>
      ) : (
        <>
          {/* Overall Maturity */}
          <div className="bg-white rounded-xl shadow-sm p-8 mb-8">
            <h2 className="text-xl font-semibold mb-6">整体成熟度</h2>
            
            <div className="flex items-center gap-6 mb-8">
              <div className="text-center">
                <div className={`w-24 h-24 rounded-full ${levelColors[currentMaturity]} flex items-center justify-center text-white text-xl font-bold`}>
                  {maturityLabels[currentMaturity]}
                </div>
                <p className="mt-2 font-medium">当前阶段</p>
              </div>
              
              <div className="flex-1">
                <div className="space-y-3">
                  {["idea", "demo", "mvp", "pre_production", "production"].map((level) => {
                    const isCurrent = level === currentMaturity
                    const levels = ["idea", "demo", "mvp", "pre_production", "production"]
                    const isPast = levels.indexOf(level) < levels.indexOf(currentMaturity)
                    return (
                      <div key={level} className="flex items-center gap-3">
                        <div className={`w-4 h-4 rounded-full ${
                          isCurrent ? 'bg-blue-600 ring-4 ring-blue-200' : 
                          isPast ? 'bg-green-500' : 'bg-gray-200'
                        }`} />
                        <span className={isCurrent ? 'font-semibold text-blue-600' : isPast ? 'text-gray-500' : 'text-gray-400'}>
                          {maturityLabels[level]}
                        </span>
                        {isCurrent && <span className="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded">当前</span>}
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* Dimension Scores */}
          {Object.keys(dimensionScores).length > 0 && (
            <div className="bg-white rounded-xl shadow-sm p-8 mb-8">
              <h2 className="text-xl font-semibold mb-6">维度评分</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {Object.entries(dimensionScores).map(([key, score]: [string, any]) => (
                  <div key={key} className="p-4 border rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium">{score.dimension || key}</span>
                      <span className={`text-sm ${levelColors[score.level]?.replace('bg-', 'text-').replace('-400', '-600')}`}>
                        {maturityLabels[score.level] || score.level}
                      </span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${levelColors[score.level] || 'bg-gray-400'} transition-all duration-500`}
                        style={{ width: `${score.progress || 0}%` }}
                      />
                    </div>
                    <div className="flex justify-between items-center mt-1">
                      <span className="text-xs text-gray-500">完成度</span>
                      <span className="text-xs font-medium">{score.progress || 0}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Identified Gaps */}
          {gaps.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm p-8 mb-8">
              <h2 className="text-xl font-semibold mb-6">识别的缺口 ({gaps.length})</h2>
              
              <div className="space-y-4">
                {gaps.slice(0, 10).map((gap: any) => (
                  <div key={gap.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <span className={`w-3 h-3 rounded-full ${
                        gap.priority === 'critical' ? 'bg-red-500' :
                        gap.priority === 'high' ? 'bg-orange-500' :
                        gap.priority === 'medium' ? 'bg-yellow-500' : 'bg-gray-400'
                      }`} />
                      <div>
                        <p className="font-medium">{gap.description}</p>
                        <p className="text-sm text-gray-500">维度: {gap.dimension}</p>
                      </div>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm ${
                      gap.priority === 'critical' ? 'bg-red-100 text-red-700' :
                      gap.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                      gap.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-700'
                    }`}>
                      {gap.priority === 'critical' ? '关键' :
                       gap.priority === 'high' ? '高' :
                       gap.priority === 'medium' ? '中' : '低'}优先级
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Project Stats */}
          {projectFacts.total_files > 0 && (
            <div className="bg-white rounded-xl shadow-sm p-8 mb-8">
              <h2 className="text-xl font-semibold mb-6">项目统计</h2>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <StatCard label="总文件数" value={projectFacts.total_files} />
                <StatCard label="代码行数" value={(projectFacts.code_lines || 0).toLocaleString()} />
                <StatCard label="测试文件" value={projectFacts.test_files || 0} />
                <StatCard label="框架" value={projectFacts.frameworks?.length || 0} />
              </div>

              {projectFacts.frameworks?.length > 0 && (
                <div className="mt-6">
                  <h3 className="font-medium mb-3">技术栈</h3>
                  <div className="flex flex-wrap gap-2">
                    {projectFacts.frameworks.map((fw: string) => (
                      <span key={fw} className="px-3 py-1 bg-gray-100 rounded-full text-sm">
                        {fw}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Next Steps */}
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-8">
            <h2 className="text-xl font-semibold mb-4">下一步</h2>
            <ul className="space-y-3">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>基于体检结果生成升级计划</span>
              </li>
            </ul>
            
            <a
              href={`/upgrade-map?project_id=${projectId}`}
              className="inline-flex items-center gap-2 mt-6 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              查看升级路线
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </a>
          </div>
        </>
      )}
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="text-center p-4 bg-gray-50 rounded-lg">
      <p className="text-3xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500 mt-1">{label}</p>
    </div>
  )
}
