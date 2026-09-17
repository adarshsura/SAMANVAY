import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { useWebSocket } from '../../context/WebSocketContext';
import { ShieldAlert, Activity, Wifi, WifiOff, LogOut, User as UserIcon, Radio, Compass, Sliders } from 'lucide-react';

interface NavbarProps {
  currentTab: 'citizen' | 'admin' | 'responder' | 'simulation' | 'login';
  onSelectTab: (tab: 'citizen' | 'admin' | 'responder' | 'simulation' | 'login') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, onSelectTab }) => {
  const { user, logout, isAuthenticated } = useAuth();
  const { isConnected } = useWebSocket();

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div 
          onClick={() => onSelectTab('citizen')}
          className="flex items-center space-x-3 cursor-pointer select-none"
        >
          <div className="w-10 h-10 rounded-lg bg-emergency-600 flex items-center justify-center shadow-lg shadow-emergency-600/30">
            <ShieldAlert className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-xl tracking-tight text-white">SAMANVAY</span>
              <span className="bg-red-500/20 text-red-400 text-xs font-semibold px-2 py-0.5 rounded border border-red-500/30">
                AI DISPATCH
              </span>
            </div>
            <p className="text-[11px] text-slate-400 -mt-0.5 hidden sm:block">
              Faster Help. Smarter Response.
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-1 sm:space-x-2">
          <button
            onClick={() => onSelectTab('citizen')}
            className={`px-3 py-1.5 rounded-md text-xs sm:text-sm font-medium transition flex items-center space-x-1.5 ${
              currentTab === 'citizen'
                ? 'bg-emergency-600 text-white shadow'
                : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <Radio className="w-4 h-4 text-red-400" />
            <span>Citizen SOS</span>
          </button>

          <button
            onClick={() => onSelectTab('admin')}
            className={`px-3 py-1.5 rounded-md text-xs sm:text-sm font-medium transition flex items-center space-x-1.5 ${
              currentTab === 'admin'
                ? 'bg-blue-600 text-white shadow'
                : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <Activity className="w-4 h-4 text-blue-400" />
            <span className="hidden sm:inline">Command Center</span>
            <span className="sm:hidden">Admin</span>
          </button>

          <button
            onClick={() => onSelectTab('responder')}
            className={`px-3 py-1.5 rounded-md text-xs sm:text-sm font-medium transition flex items-center space-x-1.5 ${
              currentTab === 'responder'
                ? 'bg-emerald-600 text-white shadow'
                : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <Compass className="w-4 h-4 text-emerald-400" />
            <span>Responder</span>
          </button>

          <button
            onClick={() => onSelectTab('simulation')}
            className={`px-3 py-1.5 rounded-md text-xs sm:text-sm font-medium transition flex items-center space-x-1.5 ${
              currentTab === 'simulation'
                ? 'bg-amber-600 text-white shadow'
                : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <Sliders className="w-4 h-4 text-amber-400" />
            <span className="hidden md:inline">Simulation</span>
          </button>
        </nav>

        {/* Live Status & User Info */}
        <div className="flex items-center space-x-3">
          {/* Live stream pill */}
          <div 
            title={isConnected ? "Real-time dispatch telemetry connected" : "Telemetry disconnected, reconnecting..."}
            className={`hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono border ${
              isConnected 
                ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-400' 
                : 'bg-amber-950/60 border-amber-500/40 text-amber-400'
            }`}
          >
            {isConnected ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>LIVE</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3 h-3" />
                <span>OFFLINE</span>
              </>
            )}
          </div>

          {/* User Account / Login */}
          {isAuthenticated && user ? (
            <div className="flex items-center space-x-2">
              <div className="text-right hidden sm:block">
                <div className="text-xs font-medium text-slate-200">{user.name || user.username}</div>
                <div className="text-[10px] font-mono text-slate-400">{user.role}</div>
              </div>
              <button
                onClick={logout}
                title="Log out"
                className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => onSelectTab('login')}
              className="text-xs font-semibold px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 transition flex items-center space-x-1"
            >
              <UserIcon className="w-3.5 h-3.5" />
              <span>Login</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
