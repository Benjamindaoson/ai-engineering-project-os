'use client'

// Mock data for upgrade map
const mockUpgradePlan = {
  current_level: "mvp",
  target_level: "pre_production",
  upgrade_path: ["pre_production", "production"],
  recommended_tasks: [
    {
      id: "task-1",
      title: "增加权限控制",
      description: "实现基于角色的访问控制(RBAC)",
      gap_id: "gap-1",
      dimension: "auth",
      priority: "critical",
      estimated_effort: "2-3天",
      status: "pending",
    },
    {
      id: "task-2",
      title: "添加监控系统",
      description: "集成日志和指标收集",
      gap_id: "gap-2",
      dimension: "monitoring",
      priority: "high",
      estimated_effort: "1-2天",
      status: "pending",
    },
    {
      id: "task-3",
      title: "提升测试覆盖率",
      description: "从25%提升到60%以上",
      gap_id: "gap-3",
      dimension: "testing",
      priority: "high",
      estimated_effort: "3-5天",
      status: "pending",
    },
    {
      id: "task-4",
      title: "完善CI/CD流程",
      description: "建立自动化构建和部署",
      gap_id: "gap-4",
      dimension: "deployment",
      priority: "medium",
      estimated_effort: "2-3天",
      status: "pending",
    },
    {
      id: "task-5",
      title: "加强输入验证",
      description: "添加请求参数验证和清理",
      gap_id: "gap-5",
      dimension: "security",
      priority: "high",
      estimated_effort: "1-2天",
      status: "pending",
    },
  ],
  prioritization_rationale: "根据生产就绪需求和项目当前状态，优先处理关键路径上的缺陷。权限控制和监控是进入准生产级的前置条件。",
  immediate_next_steps: [
    "选择「增加权限控制」作为第一个升级任务",
    "仔细阅读工程导师提供的学习内容",
    "按照任务要求修改代码",
    "运行测试验证修改",
    "让验证智能体检查是否完成",
  ],
  estimated_total_effort: "约2周",
}

export default function UpgradeMapPage() {
  const levelLabels: Record<string, string> = {
    idea: "想法",
    demo: "演示版",
    mvp: "最小可用版本",
    pre_production: "准生产级",
    production: "生产级",
  }

  const levelDescriptions: Record<string, string> = {
    idea: "只有想法或概念验证",
    demo: "核心功能可演示，但不稳定",
    mvp: "基本可用，但缺乏生产特性",
    pre_production: "接近生产，但需完善治理",
    production: "完全生产就绪",
  }

  const levels = ["idea", "demo", "mvp", "pre_production", "production"]
  const currentIndex = levels.indexOf(mockUpgradePlan.current_level)

  return (
    <div className="max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">升级地图</h1>
        <p className="text-gray-600">从当前阶段到目标的完整升级路线</p>
      </div>

      {/* Current Position */}
      <div className="bg-white rounded-xl shadow-sm p-8 mb-8">
        <div className="flex items-center gap-6 mb-6">
          <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center">
            <span className="text-2xl">📍</span>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">当前位置</p>
            <h2 className="text-2xl font-bold">{levelLabels[mockUpgradePlan.current_level]}</h2>
            <p className="text-gray-600">{levelDescriptions[mockUpgradePlan.current_level]}</p>
          </div>
        </div>

        {/* Upgrade Path */}
        <div className="flex items-center gap-4 overflow-x-auto py-4">
          {levels.map((level, index) => {
            const isPast = index < currentIndex
            const isCurrent = level === mockUpgradePlan.current_level
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
                    {levelLabels[level]}
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
      <div className="bg-white rounded-xl shadow-sm p-8 mb-8">
        <h2 className="text-xl font-semibold mb-6">推荐升级任务</h2>
        
        <div className="space-y-4">
          {mockUpgradePlan.recommended_tasks.map((task, index) => (
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
                    {task.estimated_effort}
                  </span>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-500">维度: {task.dimension}</span>
                <a
                  href={`/tasks?task_id=${task.id}`}
                  className="ml-auto px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                >
                  开始任务
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Rationale */}
      <div className="bg-gray-50 rounded-xl p-8 mb-8">
        <h2 className="text-xl font-semibold mb-4">优先级说明</h2>
        <p className="text-gray-700">{mockUpgradePlan.prioritization_rationale}</p>
      </div>

      {/* Immediate Steps */}
      <div className="bg-white rounded-xl shadow-sm p-8">
        <h2 className="text-xl font-semibold mb-6">立即行动</h2>
        <ol className="space-y-4">
          {mockUpgradePlan.immediate_next_steps.map((step, index) => (
            <li key={index} className="flex items-start gap-4">
              <span className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                {index + 1}
              </span>
              <span className="pt-1">{step}</span>
            </li>
          ))}
        </ol>
        
        <div className="mt-6 pt-6 border-t">
          <p className="text-gray-600">
            预计总工作量: <span className="font-semibold text-gray-900">{mockUpgradePlan.estimated_total_effort}</span>
          </p>
        </div>
      </div>
    </div>
  )
}
