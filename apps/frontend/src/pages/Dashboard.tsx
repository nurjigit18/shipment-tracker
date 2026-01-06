import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { shipmentService } from '../services/shipments';
import type { ShipmentListItem } from '../services/shipments';
import { Package, TrendingUp, Loader2, AlertCircle, ArrowRight, Plus } from 'lucide-react';

export function Dashboard() {
  const [shipments, setShipments] = useState<ShipmentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadShipments();
  }, []);

  const loadShipments = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await shipmentService.listShipments({ limit: 10 });
      setShipments(data);
    } catch (e: any) {
      setError(e.message || 'Ошибка загрузки отправок');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-emerald-500 animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Загрузка...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-lg border border-red-200 p-8">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-slate-900 mb-2">Ошибка загрузки</h2>
            <p className="text-slate-600 mb-6">{error}</p>
            <button
              onClick={loadShipments}
              className="px-6 py-2.5 bg-emerald-500 text-white rounded-xl hover:bg-emerald-600 transition-colors font-medium"
            >
              Попробовать снова
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Главная</h1>
        <p className="text-slate-600">Обзор ваших отправок</p>
      </div>

      {/* Stats cards - Fixed padding and alignment */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <p className="text-sm text-slate-600 mb-2">Всего отправок</p>
              <p className="text-3xl font-bold text-slate-900 truncate">{shipments.length}</p>
            </div>
            <div className="p-3 bg-emerald-50 rounded-xl flex-shrink-0">
              <Package className="w-7 h-7 text-emerald-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <p className="text-sm text-slate-600 mb-2">Всего мешков</p>
              <p className="text-3xl font-bold text-slate-900 truncate">
                {shipments.reduce((sum, s) => sum + s.total_bags, 0)}
              </p>
            </div>
            <div className="p-3 bg-blue-50 rounded-xl flex-shrink-0">
              <TrendingUp className="w-7 h-7 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <p className="text-sm text-slate-600 mb-2">Всего вещей</p>
              <p className="text-3xl font-bold text-slate-900 truncate">
                {shipments.reduce((sum, s) => sum + s.total_pieces, 0)}
              </p>
            </div>
            <div className="p-3 bg-purple-50 rounded-xl flex-shrink-0">
              <Package className="w-7 h-7 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Recent Shipments - Fixed padding */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200">
        <div className="px-6 py-5 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Последние отправки</h2>
            <p className="text-sm text-slate-600 mt-1">Ваши последние 10 отправок</p>
          </div>
          <Link
            to="/shipments"
            className="flex items-center gap-2 px-4 py-2 text-emerald-600 hover:bg-emerald-50 rounded-xl transition-colors font-medium text-sm"
          >
            <span>Смотреть все</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {shipments.length === 0 ? (
          <div className="p-12 text-center">
            <Package className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">Нет отправок</h3>
            <p className="text-slate-600 mb-6">Начните с создания вашей первой отправки</p>
            <Link
              to="/shipments/new"
              className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-500 text-white rounded-xl hover:bg-emerald-600 transition-colors font-medium"
            >
              <Plus className="w-5 h-5" />
              <span>Новая отправка</span>
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {shipments.map((shipment) => (
              <Link
                key={shipment.id}
                to={`/shipments/${shipment.id}`}
                className="block px-6 py-5 hover:bg-slate-50 transition-colors group"
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2 flex-wrap">
                      <p className="font-mono text-sm font-semibold text-slate-900">
                        {shipment.id}
                      </p>
                      <StatusBadge status={shipment.current_status} />
                    </div>
                    <p className="text-sm text-slate-600 mb-2 truncate">
                      {shipment.supplier} → {shipment.warehouse}
                    </p>
                    <div className="flex items-center gap-4 text-xs text-slate-500 flex-wrap">
                      <span className="flex items-center gap-1">
                        <Package className="w-3.5 h-3.5 flex-shrink-0" />
                        {shipment.total_bags} мешков
                      </span>
                      <span>•</span>
                      <span>{shipment.total_pieces} вещей</span>
                      <span>•</span>
                      <span className="whitespace-nowrap">
                        {new Date(shipment.created_at).toLocaleDateString('ru-RU', {
                          day: '2-digit',
                          month: 'short',
                          year: 'numeric',
                        })}
                      </span>
                    </div>
                  </div>
                  <ArrowRight className="w-5 h-5 text-slate-400 group-hover:text-emerald-600 transition-colors flex-shrink-0" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string | null }) {
  const statusConfig: Record<string, { label: string; colorClass: string }> = {
    SENT_FROM_FACTORY: { label: 'У поставщика', colorClass: 'bg-amber-100 text-amber-700 border-amber-200' },
    SHIPPED_FROM_FF: { label: 'У FF', colorClass: 'bg-blue-100 text-blue-700 border-blue-200' },
    DELIVERED: { label: 'Доставлено', colorClass: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
  };

  const config = status ? statusConfig[status] : null;

  if (!config) {
    return (
      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200 whitespace-nowrap">
        Новая
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border whitespace-nowrap ${config.colorClass}`}
    >
      {config.label}
    </span>
  );
}
