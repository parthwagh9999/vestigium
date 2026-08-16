import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/auth';
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import Investigation from '@/pages/Investigation';
import ToolCenter from '@/pages/ToolCenter';
import VulnerabilityCenter from '@/pages/VulnerabilityCenter';
import GlobalNavigation from '@/components/layout/GlobalNavigation';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100">
      <GlobalNavigation />
      <div className="flex-1 h-full w-full relative flex flex-col overflow-hidden">
        {children}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/investigation/:id"
        element={
          <ProtectedRoute>
            <Investigation />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tools"
        element={
          <ProtectedRoute>
            <ToolCenter />
          </ProtectedRoute>
        }
      />
      <Route
        path="/vulnerabilities"
        element={
          <ProtectedRoute>
            <VulnerabilityCenter />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
