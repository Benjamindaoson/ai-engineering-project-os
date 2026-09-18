'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'

// Mock data for demonstration
const mockAuditData = {
  project_facts: {
    project_name: "AIEduRAG",
    project_type: "rag",
    main_language: ["Python"],
    frameworks: ["FastAPI", "LangChain"],
    database: ["PostgreSQL", "Milvus"],
    total_files: 156,
    code_lines: 12450,
    test_files: 8,
    has_readme: true,
    has_api_docs: false,
  },
  maturity_assessment: {
    overall_level: "mvp",
    dimension_scores: {
      core_features: { dimension: "核心功能", level: "mvp", progress: 75 },
      data: { dimension: "数据层", level: "pre_production", progress: 60 },
      api: { dimension: "API层", level: "mvp", progress: 70 },
      auth: { dimension: "权限", level: "idea", progress: 0 },
      security: { dimension: "安全", level: "demo", progress: 30 },
      error_handling: { dimension: "错误处理", level: "mvp", progress: 65 },
      testing: { dimension: "测试", level: "demo", progress: 25 },
      evaluation: { dimension: "评测", level: "pre_production", progress: 55 },
      deployment: { dimension: "部署", level: "demo", progress: 40 },
      monitoring: { dimension: "监控", level: "idea", progress: 10 },
    },
    blockers: [
      { criterion_name: "权限控制", category: "auth" },
      { criterion_name: "监控", category: "monitoring" },
      { criterion_name: "自动化测试", category: "testing" },
    ],
    recommendations: [
      "需要增加权限控制",
      "建议添加监控系统",
      "测试覆盖率需要提高",
    ],
  },
  gaps: [
    { id: "1", dimension: "auth", description: "权限控制", priority: "critical" },
    { id: "2", dimension: "monitoring", description: "监控", priority: "high" },
    { id: "3", dimension: "testing", description: "自动化测试", priority: "high" },
    { id: "4", dimension: "deployment", description: "CI/CD", priority: "medium" },
    { id: "5", dimension: "security", description: "输入验证", priority: "high" },
  ],
}

export default function HealthPage() {
  const searchParams = useSearchParams()
  const projectId = searchParams.get('project_id')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState(mockAuditData)

  useEffect(() => {
    if (projectId) {
      // In production, fetch from API
      // fetchAudit(projectId)
    }
  }, [projectId])

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

  return (
    <div className="max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">项目体检</h1>
        <p className="text-gray-600">
          {data.project_facts.project_name} - 全面分析项目现状
        </p>
      </div>

      {/* Overall Maturity */}
      <div className="bg-white rounded-xl shadow-sm p-8 mb-8">
        <h2 className="text-xl font-semibold mb-6">整体成熟度</h2>
        
        <div className="flex items-center gap-6 mb-8">
          <div className="text-center">
            <div className={`w-24 h-24 rounded-full ${levelColors[data.maturity_assessment.overall_level]} flex items-center justify-center text-white text-2xl font-bold`}>
              {maturityLabels[data.maturity_assessment.overall_level]}
            </div>
            <p className="mt-2 font-medium">当前阶段</p>
          </div>
          
          <div className="flex-1">
            <div className="space-y-3">
              {["idea", "demo", "mvp", "pre_production", "production"].map((level) => {
                const isCurrent = level === data.maturity_assessment.overall_level
                const isPast = ["idea", "demo", "mvp", "pre_production", "production"].indexOf(level) < 
                              ["idea", "demo", "mvp", "pre_production", "production"].indexOf(data.maturity_assessment.overall_level)
                return (
                  <div key={level} className="flex items-center gap-3">
                    <div className={`w-4 h-4 rounded-full ${isCurrent ? 'bg-blue-600 ring-4 ring-blue-200' : isPast ? 'bg-green-500' : 'bg-gray-200'}`} />
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
      <div className="bg-white rounded-xl shadow-sm p-8 mb-8">
        <h2 className="text-xl font-semibold mb-6">维度评分</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Object.entries(data.maturity_assessment.dimension_scores).map(([key, score]: [string, any]) => (
            <div key={key} className="p-4 border rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium">{score.dimension}</span>
                <span className={`text-sm ${levelColors[score.level].replace('bg-', 'text-').replace('-400', '-600')}`}>
                  {maturityLabels[score.level]}
                </span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div 
                  className={`h-full ${levelColors[score.level]} transition-all duration-500`}
                  style={{ width: `${score.progress}%` }}
                />
              </div>
              <div className="flex justify-between items-center mt-1">
                <span className="text-xs text-gray-500">完成度</span>
                <span className="text-xs font-medium">{score.progress}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Identified Gaps */}
      <div className="bg-white rounded-xl shadow-sm p-8 mb-8">
        <h2 className="text-xl font-semibold mb-6">识别的缺口</h2>
        
        <div className="space-y-4">
          {data.gaps.map((gap: any) => (
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

      {/* Project Stats */}
      <div className="bg-white rounded-xl shadow-sm p-8 mb-8">
        <h2 className="text-xl font-semibold mb-6">项目统计</h2>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <StatCard label="总文件数" value={data.project_facts.total_files} />
          <StatCard label="代码行数" value={data.project_facts.code_lines.toLocaleString()} />
          <StatCard label="测试文件" value={data.project_facts.test_files} />
          <StatCard label="框架" value={data.project_facts.frameworks.length} />
        </div>

        <div className="mt-6">
          <h3 className="font-medium mb-3">技术栈</h3>
          <div className="flex flex-wrap gap-2">
            {data.project_facts.frameworks.map((fw: string) => (
              <span key={fw} className="px-3 py-1 bg-gray-100 rounded-full text-sm">
                {fw}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-8">
        <h2 className="text-xl font-semibold mb-4">改进建议</h2>
        <ul className="space-y-3">
          {data.maturity_assessment.recommendations.map((rec: string, i: number) => (
            <li key={i} className="flex items-start gap-3">
              <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{rec}</span>
            </li>
          ))}
        </ul>
        
        <a
          href="/upgrade-map"
          className="inline-flex items-center gap-2 mt-6 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          查看升级路线
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </a>
      </div>
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
