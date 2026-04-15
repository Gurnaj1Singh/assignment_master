import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import {
  BookOpen,
  LayoutDashboard,
  LogOut,
  FileText,
  Menu,
  Moon,
  Sun,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import { cn } from '@/lib/utils'
import useAuthStore from '@/stores/authStore'
import useThemeStore from '@/stores/themeStore'

function NavItem({ to, icon: Icon, label, onClick }) {
  const location = useLocation()
  const active = location.pathname === to || location.pathname.startsWith(to + '/')
  return (
    <Link
      to={to}
      onClick={onClick}
      className={cn(
        'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
        active
          ? 'bg-primary text-primary-foreground'
          : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
      )}
    >
      <Icon className="h-4 w-4" />
      {label}
    </Link>
  )
}

function SidebarContent({ navItems, user, onLogout, onNavClick }) {
  const { theme, toggle } = useThemeStore()

  return (
    <>
      {/* Brand */}
      <div className="flex h-14 items-center gap-2 border-b px-4">
        <BookOpen className="h-5 w-5 text-primary" />
        <span className="font-semibold tracking-tight">Assignment Master</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {navItems.map((item) => (
          <NavItem key={item.to} {...item} onClick={onNavClick} />
        ))}
      </nav>

      <Separator />

      {/* User footer */}
      <div className="space-y-2 p-3">
        {/* Theme toggle */}
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start gap-2 text-muted-foreground"
          onClick={toggle}
        >
          {theme === 'dark' ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
          {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
        </Button>

        <Separator />

        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground uppercase">
            {user?.name?.charAt(0) ?? '?'}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{user?.name}</p>
            <p className="truncate text-xs capitalize text-muted-foreground">
              {user?.role}
            </p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onLogout}
            title="Sign out"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </>
  )
}

export default function AppShell({ children }) {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)
  const isProfessor = user?.role === 'professor'

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const professorNav = [
    { to: '/professor', icon: LayoutDashboard, label: 'Dashboard' },
  ]

  const studentNav = [
    { to: '/student', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/student/submissions', icon: FileText, label: 'My Submissions' },
  ]

  const navItems = isProfessor ? professorNav : studentNav

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-60 shrink-0 flex-col border-r bg-sidebar">
        <SidebarContent
          navItems={navItems}
          user={user}
          onLogout={handleLogout}
        />
      </aside>

      {/* Mobile header + sheet */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex md:hidden h-14 items-center gap-3 border-b px-4 bg-sidebar">
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-60 p-0 flex flex-col">
              <SheetHeader className="sr-only">
                <SheetTitle>Navigation</SheetTitle>
              </SheetHeader>
              <SidebarContent
                navItems={navItems}
                user={user}
                onLogout={handleLogout}
                onNavClick={() => setMobileOpen(false)}
              />
            </SheetContent>
          </Sheet>
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            <span className="font-semibold tracking-tight text-sm">
              Assignment Master
            </span>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-4 md:p-6">{children}</div>
        </main>
      </div>
    </div>
  )
}
