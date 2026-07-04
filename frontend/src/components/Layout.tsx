import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", label: "Search", end: true },
  { to: "/collections", label: "Collections" },
  { to: "/history", label: "History" },
  { to: "/preferences", label: "Preferences" },
];

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col font-sans">
      <header className="sticky top-0 z-50 backdrop-blur-md bg-white/70 border-b border-slate-200/50 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-md">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <span className="font-bold text-xl bg-clip-text text-transparent bg-gradient-to-r from-indigo-700 to-purple-700">
              ResearchVault
            </span>
          </div>
          <nav className="flex gap-2">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-300 ${
                    isActive 
                      ? "bg-indigo-600 text-white shadow-md shadow-indigo-200 translate-y-[-1px]" 
                      : "text-slate-600 hover:bg-slate-100 hover:text-indigo-600"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
