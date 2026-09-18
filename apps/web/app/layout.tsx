import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI Engineering Project OS',
  description: 'Upgrade your AI projects from idea to production',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-gray-50">
        <div className="flex">
          {/* Sidebar */}
          <aside className="w-64 h-screen bg-gray-900 text-white fixed">
            <div className="p-6">
              <h1 className="text-xl font-bold">AI Engineering OS</h1>
              <p className="text-xs text-gray-400 mt-1">项目升级系统</p>
            </div>
            <nav className="mt-6">
              <NavLink href="/projects/import" icon="Import">项目导入</NavLink>
              <NavLink href="/projects/health" icon="Activity">项目体检</NavLink>
              <NavLink href="/upgrade-map" icon="Map">升级地图</NavLink>
              <NavLink href="/tasks" icon="CheckSquare">工程任务</NavLink>
              <NavLink href="/evidence" icon="Database">证据墙</NavLink>
              <NavLink href="/interview" icon="MessageSquare">面试工作台</NavLink>
            </nav>
          </aside>
          
          {/* Main Content */}
          <main className="ml-64 flex-1 p-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}

function NavLink({ href, icon, children }: { href: string; icon: string; children: React.ReactNode }) {
  return (
    <a
      href={href}
      className="flex items-center gap-3 px-6 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
    >
      <span className="text-sm">{children}</span>
    </a>
  )
}
