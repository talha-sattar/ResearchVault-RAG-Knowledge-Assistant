import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", label: "Search", end: true },
  { to: "/chat", label: "Chat" },
  { to: "/collections", label: "Collections" },
  { to: "/history", label: "History" },
  { to: "/preferences", label: "Preferences" },
];

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b bg-white sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-6">
          <span className="font-semibold text-lg text-indigo-700">ResearchVault</span>
          <nav className="flex gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-md text-sm font-medium ${
                    isActive ? "bg-indigo-100 text-indigo-700" : "text-slate-600 hover:bg-slate-100"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
