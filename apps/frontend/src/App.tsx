import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import { Layout } from './components/Layout';
import { AuthScreen } from './pages/AuthScreen';
import { Dashboard } from './pages/Dashboard';
import { MyShipments } from './pages/MyShipments';
import { ShipmentDetail } from './pages/ShipmentDetail';

export default function App() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-neutral-50">
        <div className="text-center">
          <div className="inline-block w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-4 text-slate-600">Загрузка...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AuthScreen />;
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/shipments" element={<MyShipments />} />
        <Route path="/shipments/new" element={<NewShipmentPlaceholder />} />
        <Route path="/shipments/:id" element={<ShipmentDetail />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

// Placeholder for New Shipment page (to be implemented later)
function NewShipmentPlaceholder() {
  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
      <div className="text-center">
        <h2 className="text-2xl font-semibold text-slate-900 mb-2">
          Новая отправка
        </h2>
        <p className="text-slate-500">
          Эта страница будет реализована позже
        </p>
      </div>
    </div>
  );
}
