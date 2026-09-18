'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function ImportPage() {
  const router = useRouter()
  const [githubUrl, setGithubUrl] = useState('')
  const [localPath, setLocalPath] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<any>(null)

  const handleImport = async () => {
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetch('/api/projects/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          github_url: githubUrl || undefined,
          local_path: localPath || undefined,
        }),
      })

      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.detail || 'Import failed')
      }

      setResult(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl">
      <h1 className="text-3xl font-bold mb-2">项目导入</h1>
      <p className="text-gray-600 mb-8">导入你的 AI 项目，开始评估和升级之旅</p>

      {/* Import Form */}
      <div className="bg-white rounded-xl shadow-sm p-8 mb-8">
        <h2 className="text-xl font-semibold mb-6">选择导入方式</h2>
        
        {/* GitHub Import */}
        <div className="mb-6 p-6 border rounded-lg">
          <h3 className="font-medium mb-4">从 GitHub 导入</h3>
          <input
            type="text"
            placeholder="https://github.com/username/repository"
            value={githubUrl}
            onChange={(e) => setGithubUrl(e.target.value)}
            className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          />
          <p className="text-sm text-gray-500 mt-2">
            支持公开仓库，系统将克隆并分析代码
          </p>
        </div>

        {/* Local Path Import */}
        <div className="mb-6 p-6 border rounded-lg">
          <h3 className="font-medium mb-4">从本地路径导入</h3>
          <input
            type="text"
            placeholder="D:\Projects\my-ai-project"
            value={localPath}
            onChange={(e) => setLocalPath(e.target.value)}
            className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          />
          <p className="text-sm text-gray-500 mt-2">
            直接分析本地项目文件，无需上传
          </p>
        </div>

        <button
          onClick={handleImport}
          disabled={loading || (!githubUrl && !localPath)}
          className="w-full py-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? '导入中...' : '开始导入'}
        </button>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}
      </div>

      {/* Result */}
      {result && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-green-800">导入成功！</h3>
              <p className="text-green-600">项目 {result.name} 已准备好分析</p>
            </div>
          </div>
          
          <div className="mt-4 p-4 bg-white rounded-lg">
            <p className="text-sm text-gray-600 mb-2">项目ID</p>
            <code className="text-sm bg-gray-100 px-2 py-1 rounded">{result.project_id}</code>
          </div>

          <div className="mt-4 p-4 bg-white rounded-lg">
            <p className="text-sm text-gray-600 mb-2">工作区路径</p>
            <code className="text-sm bg-gray-100 px-2 py-1 rounded">{result.workspace_path}</code>
          </div>

          <div className="mt-4 flex gap-3">
            <button
              onClick={() => router.push(`/projects/health?project_id=${result.project_id}`)}
              className="flex-1 py-3 bg-green-600 text-white rounded-lg font-medium text-center hover:bg-green-700 transition-colors"
            >
              立即体检
            </button>
          </div>
        </div>
      )}

      {/* Existing Projects */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">已有项目</h2>
        <ExistingProjects />
      </div>
    </div>
  )
}

function ExistingProjects() {
  const [projects, setProjects] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    try {
      const response = await fetch('/api/projects')
      const data = await response.json()
      setProjects(data.projects || [])
    } catch (err) {
      console.error('Failed to fetch projects:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-gray-500">加载中...</div>
  }

  if (projects.length === 0) {
    return <div className="text-gray-500">暂无项目</div>
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {projects.map((project) => (
        <div key={project.id} className="p-6 bg-white border rounded-xl hover:border-blue-300 transition-colors">
          <h3 className="font-semibold mb-2">{project.name}</h3>
          <p className="text-sm text-gray-500 mb-3">
            成熟度: <span className="capitalize">{project.current_maturity}</span>
          </p>
          <button
            onClick={() => window.location.href = `/projects/health?project_id=${project.id}`}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            查看详情 →
          </button>
        </div>
      ))}
    </div>
  )
}
