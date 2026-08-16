import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/api/client';
import logoUrl from '@/assets/logo.png';
import { Eye, EyeOff, Loader2 } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const { data: tokens } = await apiClient.post('/auth/login', { username, password });
      const { data: user } = await apiClient.get('/auth/me', {
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      });
      setAuth(user, tokens.access_token, tokens.refresh_token);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center gradient-mesh" style={{ background: 'var(--color-vestigium-bg)' }}>
      {/* Background effects */}
      <div className="fixed inset-0 gradient-mesh pointer-events-none" />
      <div className="fixed top-1/4 left-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="fixed bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 w-full max-w-md px-6">
        <div className="glass p-8 animate-fade-in">
          {/* Logo */}
          <div className="flex flex-col items-center mb-8">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4 animate-pulse-glow">
              <img src={logoUrl} alt="VESTIGIUM Logo" className="w-full h-full object-contain" />
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">VESTIGIUM</h1>
            <p className="text-sm mt-1" style={{ color: 'var(--color-vestigium-text-dim)' }}>
              OSINT Investigation Platform
            </p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label htmlFor="username" className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-vestigium-text-dim)' }}>
                Username or Email
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input"
                placeholder="admin"
                required
                autoFocus
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-vestigium-text-dim)' }}>
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input pr-10"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                  style={{ color: 'var(--color-vestigium-text-muted)' }}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-lg text-sm" style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'var(--color-vestigium-danger)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary w-full h-11 text-base"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Default credentials hint */}
          <div className="mt-6 pt-5" style={{ borderTop: '1px solid var(--color-vestigium-border)' }}>
            <p className="text-xs text-center" style={{ color: 'var(--color-vestigium-text-muted)' }}>
              Default credentials: <span className="font-mono" style={{ color: 'var(--color-vestigium-text-dim)' }}>admin</span> / <span className="font-mono" style={{ color: 'var(--color-vestigium-text-dim)' }}>Admin123!</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
