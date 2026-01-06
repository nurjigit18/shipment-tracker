import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { shipmentService } from '../services/shipments';
import type { ShipmentListItem } from '../services/shipments';
import { Package, Loader2, AlertCircle, Filter, Search } from 'lucide-react';

export function MyShipments() {
  const [shipments, setShipments] = useState<ShipmentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadShipments();
  }, [statusFilter]);

  const loadShipments = async () => {
    setLoading(true);
    setError('');
    try {
      const params: any = { limit: 100 };
      if (statusFilter) {
        params.status = statusFilter;
      }
      const data = await shipmentService.listShipments(params);
      setShipments(data);
    } catch (e: any) {
      setError(e.message || 'Ошибка загрузки отправок');
    } finally {
      setLoading(false);
    }
  };

  const filteredShipments = shipments.filter((shipment) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      shipment.id.toLowerCase().includes(query) ||
      shipment.supplier.toLowerCase().includes(query) ||
      shipment.warehouse.toLowerCase().includes(query)
    );
  });

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-slate-900 mb-2">Мои отправки</h1>
        <p className="text-slate-500">Полный список отправок</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Поиск
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                placeholder="ID, поставщик, склад..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Status filter */}
          <div className="md:w-64">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Статус
            </label>
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent appearance-none bg-white"
              >
                <option value="">Все</option>
                <option value="SENT_FROM_FACTORY">У поставщика</option>
                <option value="SHIPPED_FROM_FF">У FF</option>
                <option value="DELIVERED">Доставлено</option>
              </select>
            </div>
          </div>
        </div>

        {/* Results count */}
        <div className="mt-4 pt-4 border-t border-slate-100">
          <p className="text-sm text-slate-600">
            Найдено отправок: <span className="font-medium">{filteredShipments.length}</span>
          </p>
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="w-8 h-8 text-emerald-500 animate-spin mx-auto mb-4" />
            <p className="text-slate-600">Загрузка отправок...</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-white rounded-2xl shadow-sm border border-red-200 p-12">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <p className="text-slate-900 font-medium mb-2">Ошибка загрузки</p>
            <p className="text-slate-600 mb-4">{error}</p>
            <button
              onClick={loadShipments}
              className="px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600"
            >
              Попробовать снова
            </button>
          </div>
        </div>
      )}

      {/* Shipments table */}
      {!loading && !error && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          {filteredShipments.length === 0 ? (
            <div className="p-12 text-center">
              <Package className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600 mb-2">
                {searchQuery || statusFilter ? 'Ничего не найдено' : 'Нет отправок'}
              </p>
              <p className="text-sm text-slate-400">
                {searchQuery || statusFilter
                  ? 'Попробуйте изменить фильтры'
                  : 'Создайте первую отправку'}
              </p>
            </div>
          ) : (
            <>
              {/* Desktop table */}
              <div className="hidden md:block overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-50 border-b border-slate-100">
                    <tr>
                      <th className="px-6 py-4 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                        ID отправки
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Поставщик
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Склад
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Статус
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Мешки / Вещи
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Дата
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredShipments.map((shipment) => (
                      <tr
                        key={shipment.id}
                        className="hover:bg-slate-50 transition-colors"
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Link
                            to={`/shipments/${shipment.id}`}
                            className="font-mono text-sm text-emerald-600 hover:text-emerald-700 font-medium"
                          >
                            {shipment.id}
                          </Link>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900">
                          {shipment.supplier}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900">
                          {shipment.warehouse}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <StatusBadge status={shipment.current_status} />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                          {shipment.total_bags} / {shipment.total_pieces}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                          {new Date(shipment.created_at).toLocaleDateString('ru-RU', {
                            day: '2-digit',
                            month: 'short',
                            year: 'numeric',
                          })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile cards */}
              <div className="md:hidden divide-y divide-slate-100">
                {filteredShipments.map((shipment) => (
                  <Link
                    key={shipment.id}
                    to={`/shipments/${shipment.id}`}
                    className="block p-6 hover:bg-slate-50 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <p className="font-mono text-sm font-medium text-emerald-600 mb-1">
                          {shipment.id}
                        </p>
                        <p className="text-sm text-slate-500">
                          {shipment.supplier} → {shipment.warehouse}
                        </p>
                      </div>
                      <StatusBadge status={shipment.current_status} />
                    </div>
                    <div className="flex items-center gap-4 text-xs text-slate-400">
                      <span>{shipment.total_bags} мешков</span>
                      <span>•</span>
                      <span>{shipment.total_pieces} вещей</span>
                      <span>•</span>
                      <span>
                        {new Date(shipment.created_at).toLocaleDateString('ru-RU', {
                          day: '2-digit',
                          month: 'short',
                        })}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string | null }) {
  const statusConfig: Record<string, { label: string; color: string }> = {
    SENT_FROM_FACTORY: { label: 'У поставщика', color: 'amber' },
    SHIPPED_FROM_FF: { label: 'У FF', color: 'blue' },
    DELIVERED: { label: 'Доставлено', color: 'emerald' },
  };

  const config = status ? statusConfig[status] : null;

  if (!config) {
    return (
      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
        Новая
      </span>
    );
  }

  const colorClasses = {
    amber: 'bg-amber-100 text-amber-700',
    blue: 'bg-blue-100 text-blue-700',
    emerald: 'bg-emerald-100 text-emerald-700',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
        colorClasses[config.color as keyof typeof colorClasses]
      }`}
    >
      {config.label}
    </span>
  );
}
