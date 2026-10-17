import * as React from "react";
import { NavLink, Outlet } from "react-router-dom";
import { LayoutDashboard, Upload, Search, Moon, Sun, BookMarked } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";
import { Switch } from "@/components/ui/Switch";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/upload", label: "Upload", icon: Upload, end: false },
  { to: "/search", label: "Search", icon: Search, end: false },
];

export function AppLayout() {
  const { theme, toggle } = useTheme();

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--color-bg)] text-[var(--color-ink)]">
      <aside className="hidden md:flex w-64 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="flex items-center gap-2 px-6 h-16 border-b border-[var(--color-border)]">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary)] text-white">
            <BookMarked className="h-4.5 w-4.5" />
          </div>
          <span className="font-display text-lg font-semibold">Paperlight</span>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-[var(--color-primary-soft)] text-[var(--color-primary)]"
                    : "text-[var(--color-ink-soft)] hover:bg-[var(--color-surface-2)] hover:text-[var(--color-ink)]"
                )
              }
            >
              <Icon className="h-4.5 w-4.5" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-[var(--color-border)] p-4">
          <div className="flex items-center justify-between rounded-lg bg-[var(--color-surface-2)] px-3 py-2.5">
            <div className="flex items-center gap-2 text-sm text-[var(--color-ink-soft)]">
              {theme === "dark" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
              Dark mode
            </div>
            <Switch checked={theme === "dark"} onCheckedChange={toggle} />
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="md:hidden flex items-center justify-between h-14 px-4 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--color-primary)] text-white">
              <BookMarked className="h-4 w-4" />
            </div>
            <span className="font-display text-base font-semibold">Paperlight</span>
          </div>
          <Switch checked={theme === "dark"} onCheckedChange={toggle} />
        </header>

        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-6xl px-4 py-6 md:px-8 md:py-8">
            <Outlet />
          </div>
        </main>

        <nav className="md:hidden flex items-center justify-around border-t border-[var(--color-border)] bg-[var(--color-surface)] py-2">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  "flex flex-col items-center gap-0.5 px-3 py-1 text-xs",
                  isActive ? "text-[var(--color-primary)]" : "text-[var(--color-ink-soft)]"
                )
              }
            >
              <Icon className="h-5 w-5" />
              {label}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  );
}

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight">{title}</h1>
        {description && <p className="text-sm text-[var(--color-ink-soft)] mt-1">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
