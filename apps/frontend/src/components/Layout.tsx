import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Home, Package, Plus, LogOut, Menu, X, ChevronLeft, ChevronRight, Users, UserCog } from 'lucide-react';
import { useState } from 'react';

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const baseMenuItems = [
    { path: '/', icon: Home, label: 'Главная' },
    { path: '/shipments', icon: Package, label: 'Мои отправки' },
    { path: '/shipments/new', icon: Plus, label: 'Новая отправка' },
    { path: '/suppliers', icon: Users, label: 'Мои поставщики' },
  ];

  // Add Users menu item only for admin and owner roles
  const menuItems = user?.role === 'admin' || user?.role === 'owner'
    ? [...baseMenuItems, { path: '/users', icon: UserCog, label: 'Пользователи' }]
    : baseMenuItems;

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    // Exact match for specific paths to avoid matching parent routes
    if (path === '/shipments/new') {
      return location.pathname === '/shipments/new';
    }
    if (path === '/shipments') {
      return location.pathname === '/shipments' || (location.pathname.startsWith('/shipments/') && !location.pathname.startsWith('/shipments/new'));
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Sidebar - Desktop */}
      <aside
        className={`hidden md:flex flex-col bg-slate-900 text-white border-r border-slate-800 transition-all duration-300 ease-in-out ${
          sidebarCollapsed ? 'w-20' : 'w-64'
        }`}
      >
        {/* Logo/Header */}
        <div className={`p-6 border-b border-slate-800 flex items-center min-h-[88px] ${
          sidebarCollapsed ? 'justify-center' : 'justify-between'
        }`}>
          {!sidebarCollapsed && (
            <div className="flex-1 min-w-0">
              <h1 className="text-xl font-semibold truncate">Nova Eris</h1>
              <p className="text-sm text-slate-400 mt-1 truncate">Tracking System</p>
            </div>
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-2.5 hover:bg-slate-800 rounded-lg transition-all duration-200 flex-shrink-0 group"
            title={sidebarCollapsed ? 'Развернуть меню' : 'Свернуть меню'}
            aria-label={sidebarCollapsed ? 'Развернуть меню' : 'Свернуть меню'}
          >
            {sidebarCollapsed ? (
              <ChevronRight className="w-5 h-5 group-hover:scale-110 transition-transform" />
            ) : (
              <ChevronLeft className="w-5 h-5 group-hover:scale-110 transition-transform" />
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 overflow-y-auto">
          <ul className="space-y-2">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`flex items-center ${sidebarCollapsed ? 'justify-center' : 'gap-3'} px-4 py-3 rounded-xl transition-all duration-200 ${
                      active
                        ? 'bg-primary-600 text-white font-medium shadow-lg shadow-cyan-600/30'
                        : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                    }`}
                    title={sidebarCollapsed ? item.label : undefined}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0" />
                    {!sidebarCollapsed && <span className="truncate">{item.label}</span>}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* User info & logout - Fixed at bottom */}
        <div className="p-4 border-t border-slate-800 mt-auto flex-shrink-0">
          {sidebarCollapsed ? (
            <div className="flex flex-col items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-cyan-700 flex items-center justify-center text-sm font-semibold shadow-lg">
                {user?.username?.charAt(0).toUpperCase()}
              </div>
              <button
                onClick={logout}
                className="p-2 text-slate-400 hover:text-red-400 rounded-lg hover:bg-slate-800 transition-all duration-200 group"
                title="Выйти"
                aria-label="Выйти"
              >
                <LogOut className="w-5 h-5 group-hover:scale-110 transition-transform" />
              </button>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-cyan-700 flex items-center justify-center text-sm font-semibold flex-shrink-0 shadow-lg">
                  {user?.username?.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">
                    {user?.username}
                  </p>
                  <p className="text-xs text-slate-400 capitalize truncate">{user?.role}</p>
                </div>
              </div>
              <button
                onClick={logout}
                className="w-full flex items-center gap-2 px-4 py-2.5 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-all duration-200 group"
              >
                <LogOut className="w-4 h-4 group-hover:scale-110 transition-transform" />
                <span className="text-sm">Выйти</span>
              </button>
            </>
          )}
        </div>
      </aside>

      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 bg-white border-b border-slate-200 z-50 shadow-sm">
        <div className="flex items-center justify-between p-4 h-[73px]">
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-semibold text-slate-900 truncate">Nova Eris</h1>
            <p className="text-xs text-slate-500 truncate">Tracking System</p>
          </div>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors flex-shrink-0"
            aria-label={mobileMenuOpen ? 'Закрыть меню' : 'Открыть меню'}
          >
            {mobileMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Menu */}
      <aside
        className={`md:hidden fixed top-[73px] left-0 bottom-0 w-64 bg-slate-900 text-white z-40 transform transition-transform duration-300 ease-in-out shadow-2xl ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Navigation */}
        <nav className="p-4 overflow-y-auto h-[calc(100%-100px)]">
          <ul className="space-y-2">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                      active
                        ? 'bg-primary-600 text-white font-medium shadow-lg shadow-cyan-600/30'
                        : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                    }`}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0" />
                    <span className="truncate">{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* User info & logout */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-800 bg-slate-900">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-cyan-700 flex items-center justify-center text-sm font-semibold flex-shrink-0 shadow-lg">
              {user?.username?.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user?.username}
              </p>
              <p className="text-xs text-slate-400 capitalize truncate">{user?.role}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center gap-2 px-4 py-2.5 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-all duration-200 group"
          >
            <LogOut className="w-4 h-4 group-hover:scale-110 transition-transform" />
            <span className="text-sm">Выйти</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-x-hidden overflow-y-auto md:pt-0 pt-[73px] bg-slate-50">
        <div className="min-h-full">
          {children}
        </div>
      </main>
    </div>
  );
}
