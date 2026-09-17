import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { WebSocketProvider } from './context/WebSocketContext';
import { Navbar } from './components/common/Navbar';
import { OfflineBanner } from './components/common/OfflineBanner';
import { CitizenPage } from './pages/CitizenPage';
import { AdminDashboardPage } from './pages/AdminDashboardPage';
import { ResponderPage } from './pages/ResponderPage';
import { SimulationPage } from './pages/SimulationPage';
import { LoginPage } from './pages/LoginPage';

const MainLayout: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'citizen' | 'admin' | 'responder' | 'simulation' | 'login'>('citizen');
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans antialiased text-slate-900 selection:bg-red-500 selection:text-white">
      <Navbar currentTab={currentTab} onSelectTab={setCurrentTab} />
      <OfflineBanner />

      <main className="flex-1 flex flex-col">
        {currentTab === 'citizen' && <CitizenPage />}
        {currentTab === 'admin' && <AdminDashboardPage />}
        {currentTab === 'responder' && <ResponderPage />}
        {currentTab === 'simulation' && <SimulationPage onNavigateToAdmin={() => setCurrentTab('admin')} />}
        {currentTab === 'login' && <LoginPage onLoginSuccess={() => setCurrentTab('admin')} />}
      </main>
    </div>
  );
};

export function App() {
  return (
    <AuthProvider>
      <WebSocketProvider>
        <MainLayout />
      </WebSocketProvider>
    </AuthProvider>
  );
}

export default App;
