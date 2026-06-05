import { HashRouter, Routes, Route, NavLink } from "react-router-dom";
import Feed from "./pages/Feed";
import KolManagement from "./pages/KolManagement";

export default function App() {
  return (
    <HashRouter>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-100 sticky top-0 z-20 h-14 flex items-center px-4">
          <div className="max-w-2xl w-full mx-auto flex items-center justify-between">
            <span className="font-bold text-gray-900 text-base">
              📈 股票大V追踪
            </span>
            <nav className="flex gap-1">
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-blue-50 text-blue-600"
                      : "text-gray-500 hover:text-gray-800"
                  }`
                }
              >
                推文 Feed
              </NavLink>
              <NavLink
                to="/kols"
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-blue-50 text-blue-600"
                      : "text-gray-500 hover:text-gray-800"
                  }`
                }
              >
                账号管理
              </NavLink>
            </nav>
          </div>
        </header>

        <Routes>
          <Route path="/" element={<Feed />} />
          <Route path="/kols" element={<KolManagement />} />
        </Routes>
      </div>
    </HashRouter>
  );
}
