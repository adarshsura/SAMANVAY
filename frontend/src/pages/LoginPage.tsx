import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Shield, Lock, User, CheckCircle2, AlertCircle, ArrowRight } from 'lucide-react';

export const LoginPage: React.FC<{ onLoginSuccess: () => void }> = ({ onLoginSuccess }) => {
  const { login } = useAuth();
  const [username, setUsername] = useState<string>('admin');
  const [password, setPassword] = useState<string>('admin123');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Login failed');
      }

      const data = await res.json();
      login(data.access_token, {
        username: data.username,
        role: data.role as any,
        responderId: data.responder_id,
        name: data.name
      });
      onLoginSuccess();
    } catch (err: any) {
      setError(err.message || 'Authentication error');
    } finally {
      setIsLoading(false);
    }
  };

  const setPreset = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-slate-900 text-slate-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl p-6 sm:p-8 space-y-6">

        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center mx-auto shadow-lg shadow-blue-600/30">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">SAMANVAY Operations Login</h1>
          <p className="text-xs text-slate-400">
            Command Center authorities and emergency field personnel access.
          </p>
        </div>

        {error && (
          <div className="p-3 bg-red-950/70 border border-red-500/50 rounded-xl text-red-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="font-semibold text-slate-300 block mb-1">Username:</label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:ring-1 focus:ring-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="font-semibold text-slate-300 block mb-1">Password:</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:ring-1 focus:ring-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 active:scale-98 text-white font-bold rounded-xl shadow-lg transition flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            <span>{isLoading ? 'Authenticating...' : 'Sign In to Console'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* 1-Click Demo Presets */}
        <div className="border-t border-slate-700/80 pt-4 space-y-2">
          <span className="text-[11px] font-semibold text-slate-400 block uppercase tracking-wider">
            1-Click Demo Credentials:
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px]">
            <button
              type="button"
              onClick={() => setPreset('admin', 'admin123')}
              className={`p-2 rounded-lg border text-center transition ${
                username === 'admin' ? 'bg-blue-900/50 border-blue-500 text-blue-300 font-bold' : 'bg-slate-900 border-slate-700 text-slate-300 hover:bg-slate-700'
              }`}
            >
              Admin HQ
            </button>
            <button
              type="button"
              onClick={() => setPreset('responder1', 'resp123')}
              className={`p-2 rounded-lg border text-center transition ${
                username === 'responder1' ? 'bg-emerald-900/50 border-emerald-500 text-emerald-300 font-bold' : 'bg-slate-900 border-slate-700 text-slate-300 hover:bg-slate-700'
              }`}
            >
              Paramedic
            </button>
            <button
              type="button"
              onClick={() => setPreset('responder2', 'resp123')}
              className={`p-2 rounded-lg border text-center transition ${
                username === 'responder2' ? 'bg-indigo-900/50 border-indigo-500 text-indigo-300 font-bold' : 'bg-slate-900 border-slate-700 text-slate-300 hover:bg-slate-700'
              }`}
            >
              Rescue Officer
            </button>
          </div>

          <p className="text-[11px] text-slate-400 italic text-center pt-2">
            Notice: Citizens never require login to raise emergency SOS.
          </p>
        </div>

      </div>
    </div>
  );
};
