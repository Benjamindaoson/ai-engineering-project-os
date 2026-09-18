'use client'

// Mock evidence data
const mockEvidence = {
  project_name: "AIEduRAG",
  versions: [
    {
      id: "v1",
      timestamp: "2024-01-15",
      title: "初始版本",
      description: "项目创建，基本检索功能",
      maturity: "demo",
      changes: [],
      evidence_count: 5,
    },
    {
      id: "v2",
      timestamp: "2024-02-20",
      title: "加入混合检索",
      description: "关键词+向量混合检索，提升召回率",
      maturity: "demo",
      changes: [
        { file: "retrieval/hybrid.py", type: "added", purpose: "混合检索实现" },
        { file: "retrieval/bm25.py", type: "added", purpose: "BM25关键词检索" },
      ],
      evidence_count: 12,
      metrics: {
        "召回率": { before: "65%", after: "82%", improvement: "+17%" },
        "P@10": { before: "0.45", after: "0.61", improvement: "+36%" },
      },
    },
    {
      id: "v3",
      timestamp: "2024-03-10",
      title: "加入重新排序",
      description: "Cross-Encoder重排序，提升精确率",
      maturity: "mvp",
      changes: [
        { file: "retrieval/reranker.py", type: "added", purpose: "重排序模块" },
        { file: "evaluation/benchmark.py", type: "added", purpose: "评测框架" },
      ],
      evidence_count: 18,
      metrics: {
        "NDCG@10": { before: "0.52", after: "0.71", improvement: "+37%" },
        "延迟": { before: "450ms", after: "520ms", improvement: "+15%" },
      },
    },
    {
      id: "v4",
      timestamp: "2024-04-05",
      title: "加入证据门",
      description: "检索质量门控，低质量拒答",
      maturity: "mvp",
      changes: [
        { file: "core/retrieval_gate.py", type: "added", purpose: "证据门实现" },
      ],
      evidence_count: 25,
      metrics: {
        "拒答率": { value: "12%" },
        "回答准确率": { before: "78%", after: "89%", improvement: "+11%" },
      },
    },
  ],
}

export default function EvidencePage() {
  return (
    <div className="max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">证据墙</h1>
        <p className="text-gray-600">{mockEvidence.project_name} - 所有升级改造的证据记录</p>
      </div>

      {/* Timeline */}
      <div className="relative">
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200" />
        
        {mockEvidence.versions.map((version, index) => (
          <div key={version.id} className="relative pl-16 pb-12">
            {/* Timeline dot */}
            <div className={`absolute left-4 w-5 h-5 rounded-full border-4 border-white ${
              index === mockEvidence.versions.length - 1 ? 'bg-blue-600' : 'bg-green-500'
            }`} />
            
            {/* Version card */}
            <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-semibold">{version.title}</h3>
                  <p className="text-sm text-gray-500">{version.timestamp}</p>
                </div>
                <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                  {version.maturity === 'demo' ? '演示版' : '最小可用'}
                </span>
              </div>
              
              <p className="text-gray-600 mb-4">{version.description}</p>

              {/* Changes */}
              {version.changes.length > 0 && (
                <div className="mb-4">
                  <h4 className="font-medium text-sm text-gray-700 mb-2">代码变更</h4>
                  <div className="space-y-2">
                    {version.changes.map((change, i) => (
                      <div key={i} className="flex items-center gap-3 text-sm">
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          change.type === 'added' ? 'bg-green-100 text-green-700' :
                          change.type === 'modified' ? 'bg-blue-100 text-blue-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {change.type === 'added' ? '新增' : change.type === 'modified' ? '修改' : '删除'}
                        </span>
                        <code className="text-gray-600">{change.file}</code>
                        <span className="text-gray-400">-</span>
                        <span className="text-gray-500">{change.purpose}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Metrics */}
              {version.metrics && (
                <div className="mb-4">
                  <h4 className="font-medium text-sm text-gray-700 mb-2">量化指标</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {Object.entries(version.metrics).map(([key, data]: [string, any]) => (
                      <div key={key} className="p-3 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-500">{key}</p>
                        {data.before && data.after ? (
                          <div className="flex items-baseline gap-2">
                            <span className="text-lg font-semibold">{data.after}</span>
                            <span className="text-sm text-gray-400 line-through">{data.before}</span>
                            <span className="text-sm text-green-600">{data.improvement}</span>
                          </div>
                        ) : (
                          <p className="text-lg font-semibold">{data.value}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Evidence count */}
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <span className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  {version.evidence_count} 条证据
                </span>
                <button className="text-blue-600 hover:text-blue-700 font-medium">
                  查看详情
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Evidence Summary */}
      <div className="bg-white rounded-xl shadow-sm p-8 mt-8">
        <h2 className="text-xl font-semibold mb-6">证据统计</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <StatCard label="总证据数" value="60" />
          <StatCard label="代码证据" value="25" />
          <StatCard label="测试证据" value="15" />
          <StatCard label="运行证据" value="20" />
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center p-4 bg-gray-50 rounded-lg">
      <p className="text-3xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500 mt-1">{label}</p>
    </div>
  )
}
