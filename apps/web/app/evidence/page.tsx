'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'

export default function EvidencePage() {
  const searchParams = useSearchParams()
  const projectId = searchParams.get('project_id')
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [evidence, setEvidence] = useState<any[]>([])
  const [projectName, setProjectName] = useState('')

  useEffect(() => {
    const fetchData = async () => {
      if (!projectId) {
        setLoading(false)
        return
      }

      try {
        // Fetch project info
        const projectResponse = await fetch(`/api/projects/${projectId}`)
        if (projectResponse.ok) {
          const project = await projectResponse.json()
          setProjectName(project.name)
        }

        // Fetch evidence
        const evidenceResponse = await fetch(`/api/projects/${projectId}/evidence`)
        if (evidenceResponse.ok) {
          const data = await evidenceResponse.json()
          setEvidence(data.evidence || [])
        }
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [projectId])

  if (!projectId) {
    return (
      <div className="max-w-6xl">
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
          <p className="text-yellow-800">请先选择一个项目</p>
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

  const evidenceByType = evidence.reduce((acc: Record<string, any[]>, item: any) => {
    const type = item.evidence_type || 'other'
    if (!acc[type]) acc[type] = []
    acc[type].push(item)
    return acc
  }, {})

  const typeLabels: Record<string, string> = {
    code: '代码证据',
    test: '测试证据',
    run_result: '运行证据',
    benchmark: '基准测试证据',
    config: '配置证据',
    documentation: '文档证据',
  }

  return (
    <div className="max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">证据墙</h1>
        <p className="text-gray-600">{projectName || '项目'} - 所有升级改造的证据记录</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {evidence.length === 0 ? (
        <div className="bg-gray-50 rounded-xl p-8 text-center">
          <p className="text-gray-600 mb-4">暂无证据记录</p>
          <p className="text-sm text-gray-500">
            完成工程任务后，证据将自动记录在这里
          </p>
        </div>
      ) : (
        <>
          {/* Evidence Summary */}
          <div className="bg-white rounded-xl shadow-sm p-8 mb-8">
            <h2 className="text-xl font-semibold mb-6">证据统计</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {Object.entries(evidenceByType).map(([type, items]) => (
                <div key={type} className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-3xl font-bold text-gray-900">{(items as any[]).length}</p>
                  <p className="text-sm text-gray-500 mt-1">{typeLabels[type] || type}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Evidence by Type */}
          {Object.entries(evidenceByType).map(([type, items]) => (
            <div key={type} className="mb-8">
              <h3 className="text-lg font-semibold mb-4">{typeLabels[type] || type} ({(items as any[]).length})</h3>
              <div className="space-y-4">
                {(items as any[]).map((item: any) => (
                  <div key={item.id} className="bg-white rounded-xl shadow-sm p-6">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="font-semibold">{item.title || 'Untitled'}</h4>
                        <p className="text-sm text-gray-500">{item.source_path}</p>
                      </div>
                      <span className="px-2 py-1 bg-gray-100 rounded text-xs">
                        {new Date(item.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {item.description && (
                      <p className="text-gray-600 mb-3">{item.description}</p>
                    )}
                    {item.content && (
                      <pre className="bg-gray-50 p-3 rounded-lg text-sm overflow-auto max-h-40">
                        {item.content.substring(0, 500)}
                        {item.content.length > 500 && '...'}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </>
      )}

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h3 className="font-semibold text-blue-800 mb-2">关于证据墙</h3>
        <p className="text-blue-700 text-sm">
          证据墙记录了项目的所有工程改造证据，包括代码变更、测试结果、运行证据等。
          每条证据都关联到具体的项目版本和执行记录，确保工程改造的可追溯性。
        </p>
      </div>
    </div>
  )
}
