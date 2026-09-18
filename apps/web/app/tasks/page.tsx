'use client'

import { useState } from 'react'
import { useSearchParams } from 'next/navigation'

// Mock task data
const mockTask = {
  id: "task-1",
  title: "增加权限控制",
  description: "实现基于角色的访问控制(RBAC)",
  dimension: "auth",
  priority: "critical",
  estimated_effort: "2-3天",
  status: "pending",
  gap_id: "gap-1",
  learning_content: {
    problem_explanation: "当前系统没有权限控制，任何人都可以访问所有功能。这在生产环境是不可接受的。",
    why_important: "没有权限控制意味着数据泄露风险、无法满足合规要求、无法进行审计。",
    simple_solution: "在每个API端点添加简单的角色检查。",
    why_simple_not_enough: "简单检查难以扩展，代码重复多，难以审计。",
    production_approach: "使用成熟的RBAC模型，建立角色-权限映射，支持动态权限配置。",
    recommended_solution: "集成 Casbin 或类似库，建立完整的权限模型。",
    verification_method: "编写测试用例验证权限控制正确性。",
    interview_questions: [
      "你如何设计权限模型？",
      "RBAC和ABAC的区别是什么？",
      "如何防止权限提升攻击？",
    ],
  },
  completion_criteria: [
    { criterion: "添加权限检查中间件", verification_method: "检查中间件代码", evidence_type: "code" },
    { criterion: "定义角色和权限", verification_method: "检查配置文件", evidence_type: "config" },
    { criterion: "测试权限控制", verification_method: "运行测试", evidence_type: "test" },
  ],
}

export default function TasksPage() {
  const searchParams = useSearchParams()
  const taskId = searchParams.get('task_id')
  const [activeTab, setActiveTab] = useState<'details' | 'mentor' | 'execute'>('details')
  const [executing, setExecuting] = useState(false)
  const [executionResult, setExecutionResult] = useState<any>(null)

  const task = mockTask // In production, fetch based on taskId

  const handleExecute = async () => {
    setExecuting(true)
    // Simulate execution
    await new Promise(resolve => setTimeout(resolve, 2000))
    setExecutionResult({
      status: 'completed',
      changes: [
        { file_path: 'middleware/auth.py', change_type: 'added' },
        { file_path: 'models/role.py', change_type: 'added' },
      ],
      test_results: [
        { test_name: 'test_admin_access', passed: true },
        { test_name: 'test_user_restriction', passed: true },
      ],
    })
    setExecuting(false)
  }

  return (
    <div className="max-w-6xl">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
          <a href="/upgrade-map" className="hover:text-blue-600">升级地图</a>
          <span>/</span>
          <span>工程任务</span>
        </div>
        <h1 className="text-3xl font-bold mb-2">{task.title}</h1>
        <p className="text-gray-600">{task.description}</p>
      </div>

      {/* Status Bar */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <StatusItem label="维度" value={task.dimension} />
            <StatusItem label="优先级" value={task.priority === 'critical' ? '关键' : task.priority} />
            <StatusItem label="预计工时" value={task.estimated_effort} />
            <StatusItem label="状态" value={task.status === 'pending' ? '待开始' : task.status} />
          </div>
          
          {task.status === 'pending' && (
            <button
              onClick={handleExecute}
              disabled={executing}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
            >
              {executing ? '执行中...' : '开始执行'}
            </button>
          )}
        </div>
      </div>

      {/* Execution Result */}
      {executionResult && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-6 mb-8">
          <h3 className="font-semibold text-green-800 mb-4">执行完成</h3>
          <div className="space-y-2">
            <p>状态: <span className="font-medium">{executionResult.status}</span></p>
            <p>文件变更: {executionResult.changes.length} 个</p>
            <p>测试通过: {executionResult.test_results.filter((t: any) => t.passed).length}/{executionResult.test_results.length}</p>
          </div>
          <a
            href="/evidence"
            className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700"
          >
            查看证据墙
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </a>
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
                  {task.completion_criteria.map((criterion: any, i: number) => (
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
            <div className="space-y-6">
              <LearningSection title="问题是什么" content={task.learning_content.problem_explanation} />
              <LearningSection title="为什么重要" content={task.learning_content.why_important} />
              <LearningSection title="最简单的方案" content={task.learning_content.simple_solution} />
              <LearningSection title="为什么简单方案不够" content={task.learning_content.why_simple_not_enough} />
              <LearningSection title="生产环境通常怎么做" content={task.learning_content.production_approach} />
              <LearningSection title="推荐方案" content={task.learning_content.recommended_solution} />
              <LearningSection title="如何验证" content={task.learning_content.verification_method} />
              
              <div className="border-t pt-6">
                <h3 className="font-semibold mb-4">面试预览</h3>
                <div className="space-y-3">
                  {task.learning_content.interview_questions.map((q: string, i: number) => (
                    <div key={i} className="p-4 bg-blue-50 rounded-lg">
                      <p className="font-medium text-blue-800">Q{i + 1}: {q}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
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

function StatusItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="font-medium capitalize">{value}</p>
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

function LearningSection({ title, content }: { title: string; content: string }) {
  return (
    <div className="border-b pb-4">
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-gray-700">{content}</p>
    </div>
  )
}
