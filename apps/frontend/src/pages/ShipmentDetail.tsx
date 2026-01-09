import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  CheckCircle2,
  Clock,
  UserCircle,
  PackageCheck,
  Warehouse,
  Edit,
  Save,
  X,
  Plus,
  Trash2,
  ChevronDown,
  ChevronUp,
  Download,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { shipmentService } from '../services/shipments';
import { apiClient } from '../services/api';

// ---------- Interfaces ----------
interface Supplier {
  id: number;
  name: string;
}

interface WarehouseOption {
  id: number;
  name: string;
}

interface BagItem {
  model: string;
  color: string;
  sizes: Record<string, number>;
}

interface Bag {
  bag_id: string;
  items: BagItem[];
}

interface ProductOption {
  id: number;
  name: string;
}

// ---------- Utilities ----------
const ROLES: Record<string, string> = {
  supplier: 'поставщик',
  ff: 'фуллфилмент',
  driver: 'водитель',
  warehouse: 'склад',
  admin: 'администратор',
};

const STAGES = [
  {
    key: 'SENT_FROM_FACTORY' as const,
    label: 'Поставщик',
    successLabel: 'Отправлено',
    icon: CheckCircle2,
  },
  {
    key: 'SHIPPED_FROM_FF' as const,
    label: 'Фулфилмент',
    successLabel: 'Отправлено',
    icon: PackageCheck,
  },
  {
    key: 'DELIVERED' as const,
    label: 'Склад (водитель)',
    successLabel: 'Доставлено',
    icon: Warehouse,
  },
];

type Status = typeof STAGES[number]['key'] | null;

// Порядок статусов для расчёта прогресса
const ORDER: Record<string, number> = {
  NONE: -1,
  SENT_FROM_FACTORY: 0,
  SHIPPED_FROM_FF: 1,
  DELIVERED: 2,
};

// Русские подписи для текущего статуса
const STATUS_RU: Record<string, string> = {
  SENT_FROM_FACTORY: 'Отправлено от Поставщика',
  SHIPPED_FROM_FF: 'Отправлено из Фулфилмента',
  DELIVERED: 'Доставлено',
};

function classNames(...xs: Array<string | false | null | undefined>) {
  return xs.filter(Boolean).join(' ');
}

export function ShipmentDetail() {
  const { id } = useParams<{ id: string }>();
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState<any>(null);
  const [updating, setUpdating] = useState(false);

  // Edit mode state
  const [isEditMode, setIsEditMode] = useState(false);
  const [saving, setSaving] = useState(false);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [warehouses, setWarehouses] = useState<WarehouseOption[]>([]);
  const [modelOptions, setModelOptions] = useState<ProductOption[]>([]);
  const [colorOptions, setColorOptions] = useState<ProductOption[]>([]);
  const [editForm, setEditForm] = useState({
    supplier: '',
    warehouse: '',
    route_type: '',
    shipment_date: '',
  });
  const [editBags, setEditBags] = useState<Bag[]>([]);
  const [expandedBag, setExpandedBag] = useState<string | null>(null);
  const [expandedItem, setExpandedItem] = useState<string | null>(null);

  const sizes = ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL', '6XL', '7XL', '8XL'];
  const sizesRow1 = ['XS', 'S', 'M', 'L', 'XL', '2XL'];
  const sizesRow2 = ['3XL', '4XL', '5XL', '6XL', '7XL', '8XL'];

  useEffect(() => {
    if (!id) {
      setError('Shipment ID not provided');
      setLoading(false);
      return;
    }

    let ignore = false;
    const load = async () => {
      console.log('🔄 Loading shipment:', id);
      setLoading(true);
      setError('');
      try {
        const result = await shipmentService.getShipment(id);
        console.log('✅ Shipment loaded:', result);
        if (!ignore) setData(result);
      } catch (e: any) {
        console.error('❌ Error loading shipment:', e);
        if (!ignore) setError(e.message || 'Failed to load shipment');
      } finally {
        if (!ignore) setLoading(false);
      }
    };
    load();
    return () => {
      ignore = true;
    };
  }, [id]);

  // Load suppliers and warehouses when entering edit mode
  useEffect(() => {
    if (isEditMode && suppliers.length === 0) {
      loadEditData();
    }
  }, [isEditMode]);

  // Populate form when data changes and in edit mode
  useEffect(() => {
    if (data?.shipment && isEditMode) {
      setEditForm({
        supplier: data.shipment.supplier || '',
        warehouse: data.shipment.warehouse || '',
        route_type: data.shipment.route_type || 'VIA_FF',
        shipment_date: data.shipment.shipment_date || '',
      });
      // Deep copy bags data
      setEditBags(JSON.parse(JSON.stringify(data.shipment.bags || [])));
    }
  }, [data, isEditMode]);

  const loadEditData = async () => {
    try {
      const [suppliersData, warehousesData, modelsData, colorsData] = await Promise.all([
        apiClient.get<Supplier[]>('/api/suppliers/my-suppliers'),
        apiClient.get<WarehouseOption[]>('/api/warehouses'),
        apiClient.get<ProductOption[]>('/api/products/models'),
        apiClient.get<ProductOption[]>('/api/products/colors'),
      ]);
      setSuppliers(suppliersData);
      setWarehouses(warehousesData);
      setModelOptions(modelsData);
      setColorOptions(colorsData);
    } catch (e: any) {
      console.error('Error loading edit data:', e);
    }
  };

  const handleEditToggle = () => {
    if (isEditMode) {
      // Cancel edit mode - reset form
      setEditForm({
        supplier: data.shipment.supplier || '',
        warehouse: data.shipment.warehouse || '',
        route_type: data.shipment.route_type || 'VIA_FF',
        shipment_date: data.shipment.shipment_date || '',
      });
      setEditBags(JSON.parse(JSON.stringify(data.shipment.bags || [])));
    }
    setIsEditMode(!isEditMode);
    setError('');
  };

  // Bag manipulation functions
  const addBag = () => {
    const bagNumber = editBags.length + 1;
    const newBag: Bag = {
      bag_id: `BAG-${bagNumber}`,
      items: [],
    };
    setEditBags([...editBags, newBag]);
    setExpandedBag(newBag.bag_id);
  };

  const removeBag = (bagId: string) => {
    setEditBags(editBags.filter((b) => b.bag_id !== bagId));
    if (expandedBag === bagId) setExpandedBag(null);
  };

  const addItemToBag = (bagId: string) => {
    setEditBags(
      editBags.map((bag) => {
        if (bag.bag_id === bagId) {
          const newItem: BagItem = {
            model: '',
            color: '',
            sizes: {},
          };
          return { ...bag, items: [...bag.items, newItem] };
        }
        return bag;
      })
    );
  };

  const removeItemFromBag = (bagId: string, itemIndex: number) => {
    setEditBags(
      editBags.map((bag) => {
        if (bag.bag_id === bagId) {
          return {
            ...bag,
            items: bag.items.filter((_, idx) => idx !== itemIndex),
          };
        }
        return bag;
      })
    );
  };

  const updateBagItem = (bagId: string, itemIndex: number, field: keyof BagItem, value: any) => {
    setEditBags(
      editBags.map((bag) => {
        if (bag.bag_id === bagId) {
          return {
            ...bag,
            items: bag.items.map((item, idx) => {
              if (idx === itemIndex) {
                return { ...item, [field]: value };
              }
              return item;
            }),
          };
        }
        return bag;
      })
    );
  };

  const updateBagItemSize = (bagId: string, itemIndex: number, size: string, quantity: number) => {
    setEditBags(
      editBags.map((bag) => {
        if (bag.bag_id === bagId) {
          return {
            ...bag,
            items: bag.items.map((item, idx) => {
              if (idx === itemIndex) {
                const newSizes = { ...item.sizes };
                if (quantity > 0) {
                  newSizes[size] = quantity;
                } else {
                  delete newSizes[size];
                }
                return { ...item, sizes: newSizes };
              }
              return item;
            }),
          };
        }
        return bag;
      })
    );
  };

  const handleSave = async () => {
    if (!data?.shipment?.id) return;

    setSaving(true);
    setError('');

    try {
      const updates: any = {};

      // Only include changed fields
      if (editForm.supplier !== data.shipment.supplier) {
        updates.supplier = editForm.supplier;
      }
      if (editForm.warehouse !== data.shipment.warehouse) {
        updates.warehouse = editForm.warehouse;
      }
      if (editForm.route_type !== data.shipment.route_type) {
        updates.route_type = editForm.route_type;
      }
      if (editForm.shipment_date !== data.shipment.shipment_date) {
        updates.shipment_date = editForm.shipment_date;
      }

      // Check if bags changed
      const bagsChanged = JSON.stringify(editBags) !== JSON.stringify(data.shipment.bags);
      if (bagsChanged) {
        updates.bags_data = editBags;
      }

      if (Object.keys(updates).length === 0) {
        setIsEditMode(false);
        return;
      }

      await shipmentService.updateShipment(data.shipment.id, updates);

      // Reload shipment data
      const result = await shipmentService.getShipment(data.shipment.id);
      setData(result);
      setIsEditMode(false);
    } catch (e: any) {
      console.error('Error saving shipment:', e);
      setError(e.message || 'Ошибка сохранения изменений');
    } finally {
      setSaving(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!data?.shipment?.id) return;

    try {
      const token = localStorage.getItem('auth_token');
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.novaeris.net';
      const response = await fetch(`${API_BASE_URL}/api/shipments/${data.shipment.id}/pdf`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to download PDF');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `shipment_${data.shipment.id}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (e: any) {
      console.error('Error downloading PDF:', e);
      setError(e.message || 'Ошибка загрузки PDF');
    }
  };

  // All hooks must be called before any conditional returns
  const statusIdx = data?.shipment?.current_status
    ? ORDER[data.shipment.current_status]
    : ORDER.NONE;

  const nextAction = useMemo<Status>(() => {
    if (statusIdx < 0) return 'SENT_FROM_FACTORY';
    if (statusIdx === 0) return 'SHIPPED_FROM_FF';
    if (statusIdx === 1) return 'DELIVERED';
    return null;
  }, [statusIdx]);

  const roleAllows = (action: Status) => {
    if (!action || !user) return false;
    if (action === 'SENT_FROM_FACTORY')
      return user.role === 'supplier' || user.role === 'admin';
    if (action === 'SHIPPED_FROM_FF')
      return user.role === 'ff' || user.role === 'admin';
    if (action === 'DELIVERED')
      return ['driver', 'warehouse', 'admin'].includes(user.role);
    return false;
  };

  const canConfirm = roleAllows(nextAction);

  const doConfirm = async () => {
    if (!nextAction || !data) return;
    setUpdating(true);
    setError('');

    try {
      await shipmentService.updateStatus(
        data.shipment.id,
        { action: nextAction },
        crypto.randomUUID ? crypto.randomUUID() : String(Date.now())
      );

      // Optimistic update
      setData({
        ...data,
        shipment: { ...data.shipment, current_status: nextAction },
      });
    } catch (e: any) {
      setError(e.message || 'Ошибка обновления статуса');
    } finally {
      setUpdating(false);
    }
  };

  // Now we can do conditional rendering
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-4 text-slate-600">Загрузка данных отправки...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center">
            <div className="text-red-500 text-5xl mb-4">⚠️</div>
            <h2 className="text-xl font-semibold mb-2">Ошибка загрузки</h2>
            <p className="text-slate-600 mb-6">{error}</p>
            <button
              onClick={logout}
              className="px-6 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-xl"
            >
              Выйти
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!data || !data.shipment) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        Нет данных
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-full sm:max-w-xl md:max-w-3xl px-2 sm:px-4 md:px-6 py-2 sm:py-4 md:py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div className="">
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight">
            Nova Eris Tracking
          </h1>
          <p className="text-xs sm:text-sm text-slate-500">
            Статус отправки и подтверждение
          </p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3 w-full sm:w-auto">
          <div className="text-left sm:text-right flex-1 sm:flex-none">
            <div className="text-xs sm:text-sm font-medium">
              {user?.username || 'user'}{' '}
              <span className="text-slate-500">
                ({ROLES[user?.role || ''] || user?.role})
              </span>
            </div>
            <div className="text-xs text-slate-500">
              Отправка:{' '}
              <span className="font-mono">{data.shipment.id}</span>
            </div>
          </div>
          <UserCircle className="w-7 h-7 sm:w-8 sm:h-8 text-slate-400 flex-shrink-0" />
          <button
            onClick={handleDownloadPDF}
            className="flex items-center gap-1.5 text-xs rounded-lg border border-primary-500 text-primary-600 px-2 sm:px-2.5 py-1 hover:bg-primary-50 flex-shrink-0"
            title="Скачать PDF с QR-кодом"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">PDF</span>
          </button>
          {(user?.role === 'supplier' || user?.role === 'admin') && !isEditMode && (
            <button
              onClick={handleEditToggle}
              className="flex items-center gap-1.5 text-xs rounded-lg border border-primary-500 text-primary-600 px-2 sm:px-2.5 py-1 hover:bg-primary-50 flex-shrink-0"
            >
              <Edit className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Редактировать</span>
            </button>
          )}
          <button
            onClick={logout}
            className="text-xs rounded-lg border px-2 sm:px-2.5 py-1 hover:bg-slate-50 flex-shrink-0"
          >
            Выйти
          </button>
        </div>
      </div>

      {/* Error alert */}
      {error && (
        <div className="mb-4 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Shipment info + summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 sm:gap-4 mb-4 sm:mb-6">
        <div className="rounded-2xl bg-white shadow-sm border border-slate-100 p-5">
          <h2 className="font-medium mb-3">Информация об отправке</h2>
          {!isEditMode ? (
            <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
              <div className="col-span-1">
                <dt className="text-slate-500">Поставщик:</dt>
                <dd className="font-medium">{data.shipment.supplier}</dd>
              </div>
              <div className="col-span-1">
                <dt className="text-slate-500">Склад:</dt>
                <dd className="font-medium">{data.shipment.warehouse}</dd>
              </div>
              <div className="col-span-1">
                <dt className="text-slate-500">ID отправки:</dt>
                <dd className="font-mono">{data.shipment.id}</dd>
              </div>
              <div className="col-span-1">
                <dt className="text-slate-500">Маршрут:</dt>
                <dd className="font-medium">
                  {data.shipment.route_type === 'DIRECT'
                    ? 'Прямой'
                    : 'Через ФФ'}
                </dd>
              </div>
              {data.shipment.shipment_date && (
                <div className="col-span-2">
                  <dt className="text-slate-500">Дата отправки:</dt>
                  <dd className="font-medium">
                    {new Date(data.shipment.shipment_date).toLocaleDateString('ru-RU', {
                      day: '2-digit',
                      month: 'long',
                      year: 'numeric'
                    })}
                  </dd>
                </div>
              )}
            </dl>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-500 mb-1">Поставщик:</label>
                <select
                  value={editForm.supplier}
                  onChange={(e) => setEditForm({ ...editForm, supplier: e.target.value })}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                >
                  <option value="">Выберите поставщика</option>
                  {suppliers.map((s) => (
                    <option key={s.id} value={s.name}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-500 mb-1">Склад:</label>
                <select
                  value={editForm.warehouse}
                  onChange={(e) => setEditForm({ ...editForm, warehouse: e.target.value })}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                >
                  <option value="">Выберите склад</option>
                  {warehouses.map((w) => (
                    <option key={w.id} value={w.name}>
                      {w.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-500 mb-1">Маршрут:</label>
                <select
                  value={editForm.route_type}
                  onChange={(e) => setEditForm({ ...editForm, route_type: e.target.value })}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                >
                  <option value="VIA_FF">Через ФФ</option>
                  <option value="DIRECT">Прямой</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-500 mb-1">Дата отправки:</label>
                <input
                  type="date"
                  value={editForm.shipment_date}
                  max={new Date().toISOString().split('T')[0]}
                  onChange={(e) => setEditForm({ ...editForm, shipment_date: e.target.value })}
                  onClick={(e) => (e.target as HTMLInputElement).showPicker?.()}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent cursor-pointer text-sm"
                />
              </div>
              <div className="text-xs text-slate-500">
                <strong>ID отправки:</strong> <span className="font-mono">{data.shipment.id}</span>
              </div>
            </div>
          )}
        </div>
        <div className="rounded-2xl bg-white shadow-sm border border-slate-100 p-5">
          <h2 className="font-medium mb-3">Сводки</h2>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <div className="col-span-1">
              <dt className="text-slate-500">Количество пакетов:</dt>
              <dd className="font-medium">
                {data.shipment.totals?.bags ?? '—'}
              </dd>
            </div>
            <div className="col-span-1">
              <dt className="text-slate-500">Общее количество (шт):</dt>
              <dd className="font-medium">
                {data.shipment.totals?.pieces ?? '—'}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Bags strip */}
      <div className="rounded-2xl bg-white shadow-sm border border-slate-100 p-4 md:p-5 mb-6 overflow-x-auto">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-medium">Информация о пакетах</h2>
          {isEditMode && (
            <button
              onClick={addBag}
              className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              <Plus className="w-4 h-4" />
              Добавить мешок
            </button>
          )}
        </div>

        {!isEditMode ? (
          <div className="space-y-4">
            {data.shipment.bags.map((bag: any) => (
              <div key={bag.bag_id} className="border border-slate-200 rounded-lg p-4">
                <h3 className="font-semibold text-sm text-primary-600 mb-3">{bag.bag_id}</h3>
                <div className="space-y-3">
                  {bag.items.map((item: any, itemIdx: number) => (
                    <div key={itemIdx} className="text-sm">
                      <div className="font-medium text-slate-700 mb-1">
                        {item.model} - {item.color}
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {Object.entries(item.sizes).map(([size, qty]) => (
                          <span
                            key={size}
                            className="inline-flex items-center rounded-full border border-slate-300 bg-slate-50 px-2.5 py-0.5 text-xs"
                          >
                            {size}: {qty as number}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {editBags.length === 0 && (
              <div className="text-center py-8 text-slate-500 text-sm">
                Нет мешков. Нажмите "Добавить мешок" чтобы начать.
              </div>
            )}
            {editBags.map((bag, bagIdx) => (
              <div key={bag.bag_id} className="border border-slate-200 rounded-lg">
                <div
                  className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-50"
                  onClick={() => setExpandedBag(expandedBag === bag.bag_id ? null : bag.bag_id)}
                >
                  <div className="flex items-center gap-3">
                    {expandedBag === bag.bag_id ? (
                      <ChevronUp className="w-5 h-5 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-slate-400" />
                    )}
                    <h3 className="font-semibold text-sm text-primary-600">{bag.bag_id}</h3>
                    <span className="text-xs text-slate-500">
                      ({bag.items.length} {bag.items.length === 1 ? 'товар' : 'товара'})
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeBag(bag.bag_id);
                    }}
                    className="text-red-500 hover:text-red-600 p-1"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                {expandedBag === bag.bag_id && (
                  <div className="p-4 pt-0 space-y-4">
                    {bag.items.map((item, itemIdx) => (
                      <div key={itemIdx} className="border border-slate-200 rounded-lg p-3 bg-slate-50">
                        <div className="flex items-start justify-between mb-3">
                          <span className="text-xs font-medium text-slate-600">Товар #{itemIdx + 1}</span>
                          <button
                            onClick={() => removeItemFromBag(bag.bag_id, itemIdx)}
                            className="text-red-500 hover:text-red-600"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>

                        <div className="grid grid-cols-2 gap-3 mb-3">
                          <div>
                            <label className="block text-xs text-slate-600 mb-1">Модель:</label>
                            <select
                              value={item.model}
                              onChange={(e) => updateBagItem(bag.bag_id, itemIdx, 'model', e.target.value)}
                              className="w-full p-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                            >
                              <option value="">Выберите модель</option>
                              {modelOptions.map((m) => (
                                <option key={m.id} value={m.name}>
                                  {m.name}
                                </option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <label className="block text-xs text-slate-600 mb-1">Цвет:</label>
                            <select
                              value={item.color}
                              onChange={(e) => updateBagItem(bag.bag_id, itemIdx, 'color', e.target.value)}
                              className="w-full p-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                            >
                              <option value="">Выберите цвет</option>
                              {colorOptions.map((c) => (
                                <option key={c.id} value={c.name}>
                                  {c.name}
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>

                        <div>
                          <label className="block text-xs text-slate-600 mb-2">Размеры:</label>
                          <div className="space-y-2">
                            <div className="grid grid-cols-6 gap-2">
                              {sizesRow1.map((size) => (
                                <div key={size}>
                                  <label className="block text-xs text-center text-slate-500 mb-1">{size}</label>
                                  <input
                                    type="number"
                                    min="0"
                                    value={item.sizes[size] || ''}
                                    onChange={(e) =>
                                      updateBagItemSize(bag.bag_id, itemIdx, size, parseInt(e.target.value) || 0)
                                    }
                                    className="w-full p-1.5 text-sm text-center border border-slate-300 rounded focus:ring-2 focus:ring-primary-500"
                                    placeholder="0"
                                  />
                                </div>
                              ))}
                            </div>
                            <div className="grid grid-cols-6 gap-2">
                              {sizesRow2.map((size) => (
                                <div key={size}>
                                  <label className="block text-xs text-center text-slate-500 mb-1">{size}</label>
                                  <input
                                    type="number"
                                    min="0"
                                    value={item.sizes[size] || ''}
                                    onChange={(e) =>
                                      updateBagItemSize(bag.bag_id, itemIdx, size, parseInt(e.target.value) || 0)
                                    }
                                    className="w-full p-1.5 text-sm text-center border border-slate-300 rounded focus:ring-2 focus:ring-primary-500"
                                    placeholder="0"
                                  />
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}

                    <button
                      onClick={() => addItemToBag(bag.bag_id)}
                      className="w-full py-2 border-2 border-dashed border-slate-300 rounded-lg text-sm text-slate-600 hover:border-primary-400 hover:text-primary-600 hover:bg-primary-50 transition-colors"
                    >
                      + Добавить товар
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 3-stage status line */}
      <div className="rounded-2xl bg-white shadow-sm border border-slate-100 p-4 md:p-6 mb-6">
        <h2 className="font-medium mb-4">Статус отправки</h2>

        {/* Desktop view - horizontal */}
        <div className="hidden md:block relative pt-6">
          <div className="relative flex flex-row items-start justify-between">
            {/* Line 1: Node 1 -> Node 2 (connects centers at 16.67% to 50%) */}
            <div className="absolute h-0.5 bg-amber-300" style={{ left: 'calc(100% / 6)', width: 'calc(100% / 3)', top: '24px', zIndex: 0 }} />
            {statusIdx >= 1 && (
              <div className="absolute h-0.5 bg-primary-500" style={{ left: 'calc(100% / 6)', width: 'calc(100% / 3)', top: '24px', zIndex: 1 }} />
            )}

            {/* Line 2: Node 2 -> Node 3 (connects centers at 50% to 83.33%) */}
            <div className="absolute h-0.5 bg-amber-300" style={{ left: '50%', width: 'calc(100% / 3)', top: '24px', zIndex: 0 }} />
            {statusIdx >= 2 && (
              <div className="absolute h-0.5 bg-primary-500" style={{ left: '50%', width: 'calc(100% / 3)', top: '24px', zIndex: 1 }} />
            )}

            {STAGES.map((st, i) => {
              const done = statusIdx >= i;
              const Icon = st.icon;
              // Find the event for this stage
              const stageEvent = data.events?.find((e: any) => e.status === st.key);
              return (
                <div key={st.key} className="flex-1 flex flex-col items-center">
                  <motion.div
                    initial={{ scale: 0.9, opacity: 0.7 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className={classNames(
                      'relative z-10 flex items-center justify-center w-12 h-12 rounded-full ring-8',
                      done
                        ? 'bg-primary-500 text-white ring-cyan-100'
                        : 'bg-amber-300 text-white ring-amber-100'
                    )}
                  >
                    {done ? (
                      <Icon className="w-6 h-6" />
                    ) : (
                      <Clock className="w-6 h-6" />
                    )}
                  </motion.div>
                  <div className="mt-2 text-sm font-medium text-center">
                    {st.label}
                  </div>
                  <div className="mt-1 text-xs text-center">
                    {done && stageEvent ? (
                      <div className="text-primary-600">
                        <div className="font-medium">{st.successLabel}</div>
                        <div className="text-slate-500 mt-0.5">
                          {new Date(stageEvent.changed_at).toLocaleDateString('ru-RU', {
                            day: '2-digit',
                            month: 'short',
                          })}
                          {' '}
                          {new Date(stageEvent.changed_at).toLocaleTimeString('ru-RU', {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </div>
                      </div>
                    ) : done ? (
                      <div className="text-primary-600 font-medium">{st.successLabel}</div>
                    ) : null}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Mobile view - vertical with centered nodes */}
        <div className="md:hidden relative flex flex-col items-center">
          {STAGES.map((st, i) => {
            const done = statusIdx >= i;
            const Icon = st.icon;
            // Find the event for this stage
            const stageEvent = data.events?.find((e: any) => e.status === st.key);
            return (
              <div key={st.key} className="relative w-full flex flex-col items-center">
                {/* Node centered */}
                <motion.div
                  initial={{ scale: 0.9, opacity: 0.7 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className={classNames(
                    'relative z-10 flex items-center justify-center w-12 h-12 rounded-full ring-8',
                    done
                      ? 'bg-primary-500 text-white ring-cyan-100'
                      : 'bg-amber-300 text-white ring-amber-100'
                  )}
                >
                  {done ? (
                    <Icon className="w-6 h-6" />
                  ) : (
                    <Clock className="w-6 h-6" />
                  )}
                </motion.div>

                {/* Label below node */}
                <div className="mt-2 text-center">
                  <div className="text-sm font-medium text-slate-900">
                    {st.label}
                  </div>
                  {done && stageEvent ? (
                    <div className="mt-1 text-xs">
                      <div className="font-medium text-primary-600">{st.successLabel}</div>
                      <div className="text-slate-500 mt-0.5">
                        {new Date(stageEvent.changed_at).toLocaleDateString('ru-RU', {
                          day: '2-digit',
                          month: 'short',
                        })}
                        {' '}
                        {new Date(stageEvent.changed_at).toLocaleTimeString('ru-RU', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </div>
                    </div>
                  ) : done ? (
                    <div className="mt-1 text-xs text-primary-600 font-medium">{st.successLabel}</div>
                  ) : null}
                </div>

                {/* Vertical connector line between nodes */}
                {i < STAGES.length - 1 && (
                  <div
                    className={classNames(
                      'w-0.5 h-12 my-4',
                      statusIdx >= i ? 'bg-cyan-400' : 'bg-amber-300'
                    )}
                  />
                )}
              </div>
            );
          })}
        </div>

        <p className="mt-4 text-xs text-slate-500">
          Нажимая «ПОДТВЕРДИТЬ», вы подтверждаете действие на текущем этапе.
        </p>
      </div>

      {/* Confirm bar or Save/Cancel buttons */}
      {isEditMode ? (
        <div className="flex items-center justify-end gap-3">
          <button
            onClick={handleEditToggle}
            disabled={saving}
            className="flex items-center gap-2 rounded-xl px-4 py-2 sm:px-6 sm:py-3 font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            <X className="w-4 h-4" />
            Отмена
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 rounded-xl px-4 py-2 sm:px-6 sm:py-3 font-semibold bg-primary-500 hover:bg-primary-600 text-white disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      ) : (
        <div className="flex items-center justify-between gap-3">
          <div className="text-sm text-slate-500 flex items-center gap-2">
            <span className="font-medium">Текущий статус:</span>
            <span>
              {data.shipment.current_status
                ? STATUS_RU[data.shipment.current_status]
                : '—'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={doConfirm}
              disabled={!canConfirm || updating || !nextAction}
              className={classNames(
                'rounded-2xl px-3 py-2 sm:px-6 sm:py-3 font-semibold tracking-wide shadow',
                canConfirm && !updating
                  ? 'bg-primary-500 hover:bg-primary-600 text-white'
                  : 'bg-slate-200 text-slate-500 cursor-not-allowed'
              )}
              title={
                !nextAction
                  ? 'Статус завершён'
                  : !canConfirm
                  ? 'Недостаточно прав для подтверждения'
                  : 'Подтвердить'
              }
            >
              {updating ? 'ОБНОВЛЕНИЕ...' : 'ПОДТВЕРДИТЬ'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
