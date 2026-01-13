import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, ChevronDown, ChevronUp, Package, Copy, Loader2, ArrowLeft, X } from 'lucide-react';
import { shipmentService } from '../services/shipments';
import { apiClient } from '../services/api';

interface BagItem {
  model: string;
  color: string;
  sizes: Record<string, number>;
}

interface Bag {
  bag_id: string;
  items: BagItem[];
}

interface Supplier {
  id: number;
  name: string;
}

interface Warehouse {
  id: number;
  name: string;
}

interface Fulfillment {
  id: number;
  name: string;
}

interface ProductOption {
  id: number;
  name: string;
}

export function NewShipment() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Form data
  const [supplierId, setSupplierId] = useState<number | null>(null);
  const [warehouseId, setWarehouseId] = useState<number | null>(null);
  const [warehouseName, setWarehouseName] = useState<string>('');
  const [routeType, setRouteType] = useState<'DIRECT' | 'VIA_FF'>('VIA_FF');
  const [shipmentType, setShipmentType] = useState<'BAGS' | 'BOXES'>('BAGS');
  const [fulfillmentId, setFulfillmentId] = useState<number | null>(null);
  const [shipmentDate, setShipmentDate] = useState<string>('');
  const [bags, setBags] = useState<Bag[]>([]);

  // Options from API
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [fulfillments, setFulfillments] = useState<Fulfillment[]>([]);
  const [modelOptions, setModelOptions] = useState<ProductOption[]>([]);
  const [colorOptions, setColorOptions] = useState<ProductOption[]>([]);

  // UI state
  const [expandedBag, setExpandedBag] = useState<string | null>(null);
  const [expandedItem, setExpandedItem] = useState<string | null>(null);
  const [loadingData, setLoadingData] = useState(true);
  const [showAddWarehouse, setShowAddWarehouse] = useState(false);
  const [newWarehouseName, setNewWarehouseName] = useState('');
  const [removeMode, setRemoveMode] = useState(false);
  const [warehousesToRemove, setWarehousesToRemove] = useState<number[]>([]);
  const [deletingWarehouses, setDeletingWarehouses] = useState(false);

  const sizes = ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL', '6XL', '7XL', '8XL'];
  const sizesRow1 = ['XS', 'S', 'M', 'L', 'XL', '2XL'];
  const sizesRow2 = ['3XL', '4XL', '5XL', '6XL', '7XL', '8XL'];

  const getSteps = () => [
    { name: 'Основные данные', icon: '📋' },
    { name: shipmentType === 'BAGS' ? 'Мешки' : 'Коробки', icon: '📦' },
    { name: 'Проверка', icon: '✓' }
  ];

  const steps = getSteps();

  // Load data on mount
  useEffect(() => {
    loadInitialData();
  }, []);

  // Load warehouses and fulfillments when supplier changes
  useEffect(() => {
    if (supplierId) {
      loadWarehousesForSupplier();

      if (routeType === 'VIA_FF') {
        loadFulfillments();
      }
    } else {
      setWarehouses([]);
      setWarehouseId(null);
      setWarehouseName('');
      setFulfillments([]);
      setFulfillmentId(null);
    }
  }, [supplierId]);

  // Load fulfillments when route type changes
  useEffect(() => {
    if (routeType === 'VIA_FF' && supplierId) {
      loadFulfillments();
    } else {
      setFulfillments([]);
      setFulfillmentId(null);
    }
  }, [routeType]);

  const loadInitialData = async () => {
    setLoadingData(true);
    try {
      const [suppliersData, modelsData, colorsData] = await Promise.all([
        apiClient.get<Supplier[]>('/api/suppliers/my-suppliers'),
        apiClient.get<ProductOption[]>('/api/products/models'),
        apiClient.get<ProductOption[]>('/api/products/colors'),
      ]);

      setSuppliers(suppliersData);
      setModelOptions(modelsData);
      setColorOptions(colorsData);
    } catch (e: any) {
      setError(e.message || 'Ошибка загрузки данных');
    } finally {
      setLoadingData(false);
    }
  };

  const loadFulfillments = async () => {
    if (!supplierId) return;

    try {
      const supplier = suppliers.find(s => s.id === supplierId);
      if (!supplier) return;

      const data = await apiClient.get<Fulfillment[]>(`/api/fulfillments/by-supplier/${encodeURIComponent(supplier.name)}`);
      setFulfillments(data);
    } catch (e: any) {
      console.error('Error loading fulfillments:', e);
      setFulfillments([]);
    }
  };

  const loadWarehousesForSupplier = async () => {
    if (!supplierId) return;

    try {
      const supplier = suppliers.find(s => s.id === supplierId);
      if (!supplier) return;

      const data = await apiClient.get<Warehouse[]>(`/api/warehouses/by-supplier/${encodeURIComponent(supplier.name)}`);
      setWarehouses(data);
    } catch (e: any) {
      console.error('Error loading warehouses:', e);
      setWarehouses([]);
    }
  };

  const createOrGetWarehouse = async (warehouseName: string): Promise<void> => {
    if (!warehouseName.trim() || !supplierId) return;

    // Check if already exists in current list
    const existing = warehouses.find(w => w.name.toLowerCase() === warehouseName.toLowerCase());
    if (existing) {
      setWarehouseId(existing.id);
      setWarehouseName(existing.name);
      return;
    }

    try {
      const supplier = suppliers.find(s => s.id === supplierId);
      if (!supplier) return;

      const newWarehouse = await apiClient.post<Warehouse>(
        `/api/warehouses/create-and-assign?name=${encodeURIComponent(warehouseName)}&supplier_name=${encodeURIComponent(supplier.name)}`,
        {}
      );
      setWarehouses([...warehouses, newWarehouse]);
      setWarehouseId(newWarehouse.id);
      setWarehouseName(newWarehouse.name);
    } catch (e) {
      console.error('Error creating warehouse:', e);
    }
  };

  const handleAddWarehouse = async () => {
    if (!newWarehouseName.trim() || !supplierId) return;

    try {
      const supplier = suppliers.find(s => s.id === supplierId);
      if (!supplier) return;

      const newWarehouse = await apiClient.post<Warehouse>(
        `/api/warehouses/create-and-assign?name=${encodeURIComponent(newWarehouseName)}&supplier_name=${encodeURIComponent(supplier.name)}`,
        {}
      );
      setWarehouses([...warehouses, newWarehouse]);
      setWarehouseId(newWarehouse.id);
      setNewWarehouseName('');
      setShowAddWarehouse(false);
    } catch (e) {
      console.error('Error creating warehouse:', e);
    }
  };

  const handleDeleteWarehouse = async (whId: number) => {
    try {
      await apiClient.delete(`/api/warehouses/${whId}`);
      setWarehouses(warehouses.filter(w => w.id !== whId));
      if (warehouseId === whId) {
        setWarehouseId(null);
      }
    } catch (e) {
      console.error('Error deleting warehouse:', e);
    }
  };

  const toggleWarehouseForRemoval = (whId: number) => {
    console.log('Toggle warehouse for removal:', whId);
    if (warehousesToRemove.includes(whId)) {
      console.log('Removing from selection');
      setWarehousesToRemove(warehousesToRemove.filter(id => id !== whId));
    } else {
      console.log('Adding to selection');
      setWarehousesToRemove([...warehousesToRemove, whId]);
    }
  };

  const handleConfirmRemoveWarehouses = async () => {
    if (warehousesToRemove.length === 0) {
      console.log('No warehouses selected for removal');
      return;
    }

    console.log('Deleting warehouses:', warehousesToRemove);
    setDeletingWarehouses(true);

    try {
      // Delete all selected warehouses
      const deletePromises = warehousesToRemove.map(whId => {
        console.log('Deleting warehouse ID:', whId);
        return apiClient.delete(`/api/warehouses/${whId}`);
      });

      await Promise.all(deletePromises);
      console.log('All warehouses deleted successfully');

      // Update state
      setWarehouses(warehouses.filter(w => !warehousesToRemove.includes(w.id)));
      if (warehouseId && warehousesToRemove.includes(warehouseId)) {
        setWarehouseId(null);
      }

      // Exit remove mode
      setRemoveMode(false);
      setWarehousesToRemove([]);
    } catch (e: any) {
      console.error('Error deleting warehouses:', e);
      alert('Ошибка при удалении складов: ' + (e.message || 'Неизвестная ошибка'));
    } finally {
      setDeletingWarehouses(false);
    }
  };

  const handleCancelRemoveMode = () => {
    setRemoveMode(false);
    setWarehousesToRemove([]);
  };

  const addBag = () => {
    const bagNumber = bags.length + 1;
    const newBag: Bag = {
      bag_id: `B-${bagNumber}`,
      items: []
    };
    setBags([...bags, newBag]);
    setExpandedBag(newBag.bag_id);
  };

  const duplicateBag = (bagId: string) => {
    const bagToDuplicate = bags.find(b => b.bag_id === bagId);
    if (!bagToDuplicate) return;

    const bagNumber = bags.length + 1;
    const newBag: Bag = {
      bag_id: `B-${bagNumber}`,
      items: bagToDuplicate.items.map(item => ({ ...item, sizes: { ...item.sizes } }))
    };
    setBags([...bags, newBag]);
    setExpandedBag(newBag.bag_id);
  };

  const removeBag = (bagId: string) => {
    // Remove the bag and renumber all remaining bags
    const filteredBags = bags.filter(b => b.bag_id !== bagId);
    const renumberedBags = filteredBags.map((bag, index) => ({
      ...bag,
      bag_id: `B-${index + 1}`
    }));
    setBags(renumberedBags);
  };

  const duplicateItem = (bagId: string, itemIndex: number) => {
    setBags(bags.map(bag => {
      if (bag.bag_id === bagId) {
        const itemToDuplicate = bag.items[itemIndex];
        const duplicatedItem = {
          ...itemToDuplicate,
          sizes: { ...itemToDuplicate.sizes }
        };
        const newItems = [...bag.items];
        newItems.splice(itemIndex + 1, 0, duplicatedItem);
        return { ...bag, items: newItems };
      }
      return bag;
    }));
  };

  const addItemToBag = (bagId: string) => {
    setBags(bags.map(bag => {
      if (bag.bag_id === bagId) {
        return {
          ...bag,
          items: [...bag.items, { model: '', color: '', sizes: {} }]
        };
      }
      return bag;
    }));
  };

  const removeItemFromBag = (bagId: string, itemIndex: number) => {
    setBags(bags.map(bag => {
      if (bag.bag_id === bagId) {
        return {
          ...bag,
          items: bag.items.filter((_, i) => i !== itemIndex)
        };
      }
      return bag;
    }));
  };

  const updateBagItem = (bagId: string, itemIndex: number, field: 'model' | 'color', value: string) => {
    setBags(bags.map(bag => {
      if (bag.bag_id === bagId) {
        const newItems = [...bag.items];
        newItems[itemIndex] = { ...newItems[itemIndex], [field]: value };
        return { ...bag, items: newItems };
      }
      return bag;
    }));
  };

  const updateItemSize = (bagId: string, itemIndex: number, size: string, value: string) => {
    setBags(bags.map(bag => {
      if (bag.bag_id === bagId) {
        const newItems = [...bag.items];
        const newSizes = { ...newItems[itemIndex].sizes };
        const numValue = parseInt(value) || 0;

        if (numValue === 0 || value === '') {
          delete newSizes[size];
        } else {
          newSizes[size] = numValue;
        }

        newItems[itemIndex] = { ...newItems[itemIndex], sizes: newSizes };
        return { ...bag, items: newItems };
      }
      return bag;
    }));
  };

  const createOrGetModel = async (modelName: string): Promise<void> => {
    if (!modelName.trim()) return;

    // Check if already exists
    const existing = modelOptions.find(m => m.name.toLowerCase() === modelName.toLowerCase());
    if (existing) return;

    try {
      const newModel = await apiClient.post<ProductOption>('/api/products/models?name=' + encodeURIComponent(modelName), {});
      setModelOptions([...modelOptions, newModel]);
    } catch (e) {
      console.error('Error creating model:', e);
    }
  };

  const createOrGetColor = async (colorName: string): Promise<void> => {
    if (!colorName.trim()) return;

    // Check if already exists
    const existing = colorOptions.find(c => c.name.toLowerCase() === colorName.toLowerCase());
    if (existing) return;

    try {
      const newColor = await apiClient.post<ProductOption>('/api/products/colors?name=' + encodeURIComponent(colorName), {});
      setColorOptions([...colorOptions, newColor]);
    } catch (e) {
      console.error('Error creating color:', e);
    }
  };

  const calculateBagTotal = (bag: Bag) => {
    return bag.items.reduce((sum, item) => {
      return sum + Object.values(item.sizes).reduce((s, qty) => s + (qty || 0), 0);
    }, 0);
  };

  const calculateTotal = () => {
    return bags.reduce((sum, bag) => sum + calculateBagTotal(bag), 0);
  };

  const canProceed = () => {
    if (step === 0) {
      const basicRequirements = supplierId !== null && warehouseId !== null;
      // If route is VIA_FF, also require fulfillment
      if (routeType === 'VIA_FF') {
        return basicRequirements && fulfillmentId !== null;
      }
      return basicRequirements;
    }
    if (step === 1) return bags.length > 0 && bags.every(bag => bag.items.length > 0 && bag.items.every(item => item.model && item.color && Object.keys(item.sizes).length > 0));
    return true;
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');

    const supplier = suppliers.find(s => s.id === supplierId);
    const warehouse = warehouses.find(w => w.id === warehouseId);
    const fulfillment = fulfillmentId ? fulfillments.find(f => f.id === fulfillmentId) : null;

    if (!supplier || !warehouse) {
      setError('Поставщик или склад не найден');
      setLoading(false);
      return;
    }

    if (routeType === 'VIA_FF' && !fulfillment) {
      setError('Выберите фулфилмент');
      setLoading(false);
      return;
    }

    try {
      await shipmentService.createShipment({
        supplier: supplier.name,
        warehouse: warehouse.name,
        route_type: routeType,
        shipment_type: shipmentType,
        fulfillment: fulfillment?.name || null,
        shipment_date: shipmentDate || null,
        bags_data: bags.map(bag => ({
          bag_id: bag.bag_id,
          items: bag.items.map(item => ({
            model: item.model,
            color: item.color,
            sizes: item.sizes
          }))
        }))
      });

      navigate('/shipments');
    } catch (e: any) {
      setError(e.message || 'Ошибка при создании отправки');
      setLoading(false);
    }
  };

  if (loadingData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Загрузка данных...</p>
        </div>
      </div>
    );
  }

  const renderBasicInfoStep = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-900">Основные данные</h2>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Поставщик *
          </label>
          <select
            value={supplierId || ''}
            onChange={(e) => setSupplierId(Number(e.target.value))}
            className="w-full p-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="">Выберите поставщика</option>
            {suppliers.map(supplier => (
              <option key={supplier.id} value={supplier.id}>{supplier.name}</option>
            ))}
          </select>
          {suppliers.length === 0 && (
            <p className="text-sm text-amber-600 mt-1">У вас нет назначенных поставщиков</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Склад назначения *
          </label>

          {!supplierId ? (
            <p className="text-sm text-slate-500 p-3 border border-slate-200 rounded-xl bg-slate-50">
              Сначала выберите поставщика, чтобы увидеть доступные склады
            </p>
          ) : (
            <>
              {/* Action buttons */}
              {warehouses.length > 0 && !showAddWarehouse && !removeMode && (
                <div className="flex gap-2 mb-3">
                  <button
                    type="button"
                    onClick={() => setShowAddWarehouse(true)}
                    className="px-3 py-2 text-sm border-2 border-dashed border-slate-300 rounded-lg hover:border-primary-400 hover:bg-cyan-50 text-slate-600 hover:text-primary-600 transition-all flex items-center gap-1"
                  >
                    <Plus size={16} />
                    Добавить
                  </button>
                  <button
                    type="button"
                    onClick={() => setRemoveMode(true)}
                    className="px-3 py-2 text-sm border-2 border-red-300 rounded-lg hover:border-red-400 hover:bg-red-50 text-red-600 hover:text-red-700 transition-all flex items-center gap-1"
                  >
                    <Trash2 size={16} />
                    Удалить
                  </button>
                </div>
              )}

              {/* Remove mode controls */}
              {removeMode && (
                <div className="mb-3 p-3 bg-red-50 border-2 border-red-200 rounded-xl">
                  <p className="text-sm text-red-700 mb-2 font-medium">
                    Выберите склады для удаления ({warehousesToRemove.length} выбрано)
                  </p>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={handleConfirmRemoveWarehouses}
                      disabled={warehousesToRemove.length === 0 || deletingWarehouses}
                      className="px-4 py-2 bg-red-900 text-white font-bold rounded-lg hover:bg-black active:bg-black active:scale-95 disabled:bg-slate-300 disabled:text-slate-500 disabled:cursor-not-allowed text-sm transition-all shadow-lg border-2 border-red-950 flex items-center gap-2"
                    >
                      {deletingWarehouses ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Удаление...
                        </>
                      ) : (
                        <>
                          <Trash2 size={16} />
                          Удалить выбранные
                        </>
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={handleCancelRemoveMode}
                      disabled={deletingWarehouses}
                      className="px-4 py-2 border-2 border-slate-300 rounded-lg hover:bg-slate-50 active:bg-slate-100 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed text-sm transition-all text-slate-700 font-medium"
                    >
                      Отмена
                    </button>
                  </div>
                </div>
              )}

              {/* Add warehouse form */}
              {showAddWarehouse && (
                <div className="mb-3 flex gap-2">
                  <input
                    type="text"
                    value={newWarehouseName}
                    onChange={(e) => setNewWarehouseName(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddWarehouse()}
                    placeholder="Название склада"
                    autoFocus
                    className="flex-1 p-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                  <button
                    type="button"
                    onClick={handleAddWarehouse}
                    className="px-4 py-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors"
                  >
                    Сохранить
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowAddWarehouse(false);
                      setNewWarehouseName('');
                    }}
                    className="px-4 py-3 border border-slate-300 rounded-xl hover:bg-slate-50 transition-colors"
                  >
                    Отмена
                  </button>
                </div>
              )}

              {/* Warehouses grid */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {warehouses.map(wh => (
                  <button
                    key={wh.id}
                    type="button"
                    onClick={() => removeMode ? toggleWarehouseForRemoval(wh.id) : setWarehouseId(wh.id)}
                    className={`p-3 rounded-xl border-2 transition-all ${
                      removeMode
                        ? warehousesToRemove.includes(wh.id)
                          ? 'border-red-500 bg-red-50 text-red-700 font-medium'
                          : 'border-slate-300 hover:border-red-300 text-slate-700'
                        : warehouseId === wh.id
                          ? 'border-primary-500 bg-cyan-50 text-cyan-700 font-medium'
                          : 'border-slate-300 hover:border-slate-400 text-slate-700'
                    }`}
                  >
                    {wh.name}
                  </button>
                ))}

                {/* Add Warehouse Button - shown when no warehouses */}
                {warehouses.length === 0 && !showAddWarehouse && (
                  <button
                    type="button"
                    onClick={() => setShowAddWarehouse(true)}
                    className="p-3 rounded-xl border-2 border-dashed border-slate-300 hover:border-primary-400 hover:bg-cyan-50 text-slate-600 hover:text-primary-600 transition-all flex items-center justify-center gap-2"
                  >
                    <Plus size={18} />
                    Добавить
                  </button>
                )}
              </div>

              {warehouses.length === 0 && !showAddWarehouse && (
                <p className="text-sm text-amber-600 mt-2">Нет складов для этого поставщика. Нажмите "Добавить", чтобы создать новый.</p>
              )}
            </>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Тип маршрута
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setRouteType('VIA_FF')}
              className={`p-4 rounded-xl border-2 transition-all ${
                routeType === 'VIA_FF'
                  ? 'border-primary-500 bg-cyan-50 text-cyan-700 font-medium'
                  : 'border-slate-200 hover:border-slate-300 text-slate-700'
              }`}
            >
              <div className="text-sm font-semibold mb-1">Через Фулфилмент</div>
              <div className="text-xs opacity-75">Поставщик → FF → Склад</div>
            </button>
            <button
              onClick={() => setRouteType('DIRECT')}
              className={`p-4 rounded-xl border-2 transition-all ${
                routeType === 'DIRECT'
                  ? 'border-primary-500 bg-cyan-50 text-cyan-700 font-medium'
                  : 'border-slate-200 hover:border-slate-300 text-slate-700'
              }`}
            >
              <div className="text-sm font-semibold mb-1">Прямая доставка</div>
              <div className="text-xs opacity-75">Поставщик → Склад</div>
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Тип упаковки
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setShipmentType('BAGS')}
              className={`p-4 rounded-xl border-2 transition-all ${
                shipmentType === 'BAGS'
                  ? 'border-primary-500 bg-cyan-50 text-cyan-700 font-medium'
                  : 'border-slate-200 hover:border-slate-300 text-slate-700'
              }`}
            >
              <div className="text-sm font-semibold mb-1">Мешки</div>
              <div className="text-xs opacity-75">Товары в мешках</div>
            </button>
            <button
              onClick={() => setShipmentType('BOXES')}
              className={`p-4 rounded-xl border-2 transition-all ${
                shipmentType === 'BOXES'
                  ? 'border-primary-500 bg-cyan-50 text-cyan-700 font-medium'
                  : 'border-slate-200 hover:border-slate-300 text-slate-700'
              }`}
            >
              <div className="text-sm font-semibold mb-1">Коробки</div>
              <div className="text-xs opacity-75">Товары в коробках</div>
            </button>
          </div>
        </div>

        {routeType === 'VIA_FF' && (
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Выберите фулфилмент *
            </label>
            <select
              value={fulfillmentId || ''}
              onChange={(e) => setFulfillmentId(Number(e.target.value))}
              className="w-full p-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">Выберите фулфилмент</option>
              {fulfillments.map(fulfillment => (
                <option key={fulfillment.id} value={fulfillment.id}>{fulfillment.name}</option>
              ))}
            </select>
            {fulfillments.length === 0 && supplierId && (
              <p className="text-sm text-amber-600 mt-1">Нет доступных фулфилментов для этого поставщика</p>
            )}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Дата отправки
          </label>
          <input
            type="date"
            value={shipmentDate}
            max={new Date().toISOString().split('T')[0]}
            onChange={(e) => setShipmentDate(e.target.value)}
            onClick={(e) => (e.target as HTMLInputElement).showPicker?.()}
            className="w-full p-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent cursor-pointer"
          />
        </div>
      </div>
    </div>
  );

  const renderBagsStep = () => {
    const containerSingular = shipmentType === 'BAGS' ? 'мешок' : 'коробку';
    const containerPlural = shipmentType === 'BAGS' ? 'мешков' : 'коробок';
    const containerNominativePlural = shipmentType === 'BAGS' ? 'Мешки' : 'Коробки';
    const containerGenitivePlural = shipmentType === 'BAGS' ? 'мешков' : 'коробок';

    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-slate-900">{containerNominativePlural}</h2>
          <div className="text-sm text-slate-600">
            <span className="font-semibold">{calculateTotal()}</span> вещей •
            <span className="font-semibold ml-2">{bags.length}</span> {containerGenitivePlural}
          </div>
        </div>

        {/* Add Bag Button */}
        <button
          onClick={addBag}
          className="w-full p-4 bg-cyan-50 border-2 border-dashed border-primary-300 rounded-xl text-primary-600 hover:bg-cyan-100 hover:border-cyan-400 transition-all flex items-center justify-center gap-2 font-medium"
        >
          <Plus size={20} /> Добавить {containerSingular}
        </button>

        {/* Bags List */}
        <div className="space-y-3">
          {bags.map((bag, bagIndex) => (
            <div key={bag.bag_id} className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm">
              <div className="w-full p-4 hover:bg-slate-50 flex items-center justify-between transition-colors">
                <div
                  className="flex items-center gap-3 flex-1 cursor-pointer"
                  onClick={() => setExpandedBag(expandedBag === bag.bag_id ? null : bag.bag_id)}
                >
                  <Package className="text-primary-500 flex-shrink-0" size={20} />
                  <div className="text-left">
                    <span className="font-mono text-sm font-semibold text-slate-900 block">{bag.bag_id}</span>
                    <span className="text-xs text-slate-500">
                      {bag.items.length} товаров • {calculateBagTotal(bag)} вещей
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => duplicateBag(bag.bag_id)}
                    className="p-2 hover:bg-blue-100 rounded-lg transition-colors"
                    title={`Дублировать ${containerSingular}`}
                  >
                    <Copy size={16} className="text-blue-600" />
                  </button>
                  {bags.length > 1 && (
                    <button
                      onClick={() => removeBag(bag.bag_id)}
                      className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                      title={`Удалить ${containerSingular}`}
                    >
                      <Trash2 size={16} className="text-red-600" />
                    </button>
                  )}
                  <button
                    onClick={() => setExpandedBag(expandedBag === bag.bag_id ? null : bag.bag_id)}
                    className="p-2"
                  >
                    {expandedBag === bag.bag_id ? (
                      <ChevronUp size={20} className="text-slate-400" />
                    ) : (
                      <ChevronDown size={20} className="text-slate-400" />
                    )}
                  </button>
                </div>
              </div>

              {expandedBag === bag.bag_id && (
                <div className="p-4 bg-slate-50 border-t border-slate-200 space-y-3">
                  {/* Items in this bag */}
                  {bag.items.map((item, itemIndex) => (
                    <div key={itemIndex} className="bg-white p-4 rounded-lg border border-slate-200">
                      <div className="flex items-start justify-between mb-3">
                        <h4 className="text-sm font-semibold text-slate-700">Товар #{itemIndex + 1}</h4>
                        <div className="flex gap-1">
                          <button
                            onClick={() => duplicateItem(bag.bag_id, itemIndex)}
                            className="p-1 hover:bg-blue-100 rounded transition-colors"
                            title="Дублировать товар"
                          >
                            <Copy size={16} className="text-blue-600" />
                          </button>
                          <button
                            onClick={() => removeItemFromBag(bag.bag_id, itemIndex)}
                            className="p-1 hover:bg-red-100 rounded transition-colors"
                            title="Удалить товар"
                          >
                            <X size={16} className="text-red-600" />
                          </button>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-2 mb-2">
                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-0.5">Модель *</label>
                          <input
                            type="text"
                            list={`models-${bagIndex}-${itemIndex}`}
                            value={item.model}
                            onChange={(e) => updateBagItem(bag.bag_id, itemIndex, 'model', e.target.value)}
                            onBlur={(e) => createOrGetModel(e.target.value)}
                            placeholder="Например: рубашка"
                            className="w-full p-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                          />
                          <datalist id={`models-${bagIndex}-${itemIndex}`}>
                            {modelOptions.map(model => (
                              <option key={model.id} value={model.name} />
                            ))}
                          </datalist>
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-0.5">Цвет *</label>
                          <input
                            type="text"
                            list={`colors-${bagIndex}-${itemIndex}`}
                            value={item.color}
                            onChange={(e) => updateBagItem(bag.bag_id, itemIndex, 'color', e.target.value)}
                            onBlur={(e) => createOrGetColor(e.target.value)}
                            placeholder="Например: красный"
                            className="w-full p-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                          />
                          <datalist id={`colors-${bagIndex}-${itemIndex}`}>
                            {colorOptions.map(color => (
                              <option key={color.id} value={color.name} />
                            ))}
                          </datalist>
                        </div>
                      </div>

                      {/* Sizes for this item - 2 rows layout */}
                      <div>
                        <label className="block text-xs font-medium text-slate-600 mb-1">Размеры *</label>
                        <div className="flex flex-col gap-1">
                          {/* Row 1: XS to 2XL */}
                          <div className="flex gap-1">
                            {sizesRow1.map(size => (
                              <div key={size} className="flex-1">
                                <div className="text-xs font-medium text-slate-700 mb-0.5 text-center">{size}</div>
                                <input
                                  type="number"
                                  min="0"
                                  value={item.sizes[size] || ''}
                                  onChange={(e) => updateItemSize(bag.bag_id, itemIndex, size, e.target.value)}
                                  className="w-full p-1 border-2 border-slate-300 rounded text-sm text-center focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                  placeholder="0"
                                />
                              </div>
                            ))}
                          </div>
                          {/* Row 2: 3XL to 8XL */}
                          <div className="flex gap-1">
                            {sizesRow2.map(size => (
                              <div key={size} className="flex-1">
                                <div className="text-xs font-medium text-slate-700 mb-0.5 text-center">{size}</div>
                                <input
                                  type="number"
                                  min="0"
                                  value={item.sizes[size] || ''}
                                  onChange={(e) => updateItemSize(bag.bag_id, itemIndex, size, e.target.value)}
                                  className="w-full p-1 border-2 border-slate-300 rounded text-sm text-center focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                                  placeholder="0"
                                />
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* Item summary */}
                      {Object.keys(item.sizes).length > 0 && (
                        <div className="mt-3 pt-3 border-t border-slate-200">
                          <div className="flex items-center gap-2 text-xs text-slate-600">
                            <span className="font-medium">Итого:</span>
                            {Object.entries(item.sizes).map(([size, qty]) => (
                              qty > 0 && (
                                <span key={size} className="px-2 py-0.5 bg-cyan-100 text-cyan-700 rounded">
                                  {size}: {qty}
                                </span>
                              )
                            ))}
                            <span className="ml-auto font-semibold">
                              {Object.values(item.sizes).reduce((s, q) => s + q, 0)} шт
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}

                  {/* Add Item Button */}
                  <button
                    onClick={() => addItemToBag(bag.bag_id)}
                    className="w-full p-3 border-2 border-dashed border-slate-300 rounded-lg text-slate-600 hover:bg-slate-100 hover:border-slate-400 transition-all flex items-center justify-center gap-2 text-sm font-medium"
                  >
                    <Plus size={16} /> Добавить товар в {containerSingular}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>

        {bags.length === 0 && (
          <div className="p-12 text-center border-2 border-dashed border-slate-200 rounded-xl">
            <Package className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">Нет {containerGenitivePlural}</h3>
            <p className="text-slate-600 mb-6">Добавьте {shipmentType === 'BAGS' ? 'первый мешок' : 'первую коробку'} в отправку</p>
          </div>
        )}
      </div>
    );
  };

  const renderReviewStep = () => {
    const supplier = suppliers.find(s => s.id === supplierId);
    const warehouse = warehouses.find(w => w.id === warehouseId);
    const fulfillment = fulfillmentId ? fulfillments.find(f => f.id === fulfillmentId) : null;
    const containerPlural = shipmentType === 'BAGS' ? 'Мешков' : 'Коробок';

    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-slate-900">Проверка отправки</h2>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
            {error}
          </div>
        )}

        <div className="bg-cyan-50 border border-cyan-200 rounded-xl p-6 space-y-3">
          <div className="flex justify-between py-2">
            <span className="font-medium text-slate-700">Поставщик:</span>
            <span className="font-semibold text-slate-900">{supplier?.name}</span>
          </div>
          <div className="flex justify-between py-2 border-t border-cyan-200">
            <span className="font-medium text-slate-700">Склад:</span>
            <span className="font-semibold text-slate-900">{warehouse?.name}</span>
          </div>
          <div className="flex justify-between py-2 border-t border-cyan-200">
            <span className="font-medium text-slate-700">Маршрут:</span>
            <span className="font-semibold text-slate-900">
              {routeType === 'VIA_FF' ? 'Через Фулфилмент' : 'Прямая доставка'}
            </span>
          </div>
          {fulfillment && (
            <div className="flex justify-between py-2 border-t border-cyan-200">
              <span className="font-medium text-slate-700">Фулфилмент:</span>
              <span className="font-semibold text-slate-900">{fulfillment.name}</span>
            </div>
          )}
          <div className="flex justify-between py-2 border-t border-cyan-200">
            <span className="font-medium text-slate-700">Тип упаковки:</span>
            <span className="font-semibold text-slate-900">
              {shipmentType === 'BAGS' ? 'Мешки' : 'Коробки'}
            </span>
          </div>
          {shipmentDate && (
            <div className="flex justify-between py-2 border-t border-cyan-200">
              <span className="font-medium text-slate-700">Дата отправки:</span>
              <span className="font-semibold text-slate-900">
                {new Date(shipmentDate).toLocaleDateString('ru-RU', {
                  day: '2-digit',
                  month: 'long',
                  year: 'numeric'
                })}
              </span>
            </div>
          )}
        </div>

        <div className="bg-slate-50 border border-slate-200 rounded-xl p-6">
          <div className="grid grid-cols-2 gap-6 text-center">
            <div>
              <div className="text-4xl font-bold text-primary-600 mb-1">{bags.length}</div>
              <div className="text-sm text-slate-600 font-medium">{containerPlural}</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary-600 mb-1">{calculateTotal()}</div>
              <div className="text-sm text-slate-600 font-medium">Всего вещей</div>
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <h3 className="font-semibold text-slate-800 text-lg">Детальная информация:</h3>
          {bags.map(bag => (
            <div key={bag.bag_id} className="border border-slate-200 rounded-xl p-4 bg-white">
              <div className="font-mono text-sm font-semibold text-primary-600 mb-3">{bag.bag_id}</div>

              {bag.items.map((item, idx) => (
                <div key={idx} className="mb-3 pb-3 border-b border-slate-100 last:border-0 last:mb-0 last:pb-0">
                  <div className="text-sm font-medium text-slate-700 mb-2">
                    {item.model} - {item.color}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(item.sizes).map(([size, qty]) => (
                      qty > 0 && (
                        <span key={size} className="px-2.5 py-1 bg-slate-100 text-slate-700 rounded text-sm">
                          {size}: {qty}
                        </span>
                      )
                    ))}
                  </div>
                </div>
              ))}

              <div className="mt-3 pt-3 border-t border-slate-200 text-sm text-slate-600">
                Всего в {shipmentType === 'BAGS' ? 'мешке' : 'коробке'}: <span className="font-semibold">{calculateBagTotal(bag)}</span> вещей
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-full bg-slate-50">
      <div className="max-w-4xl mx-auto p-6 md:p-8">
        {/* Header */}
        <div className="mb-6 flex items-center gap-4">
          <button
            onClick={() => navigate('/shipments')}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
            title="Назад"
          >
            <ArrowLeft className="w-5 h-5 text-slate-600" />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Новая отправка</h1>
            <p className="text-slate-600 mt-1">Создайте новую отправку товаров</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
          <div className="flex items-center justify-between">
            {steps.map((s, i) => (
              <React.Fragment key={i}>
                <div className="flex flex-col items-center flex-1">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xl transition-all ${
                    i <= step ? 'bg-primary-500 text-white shadow-lg shadow-cyan-500/30' : 'bg-slate-200 text-slate-500'
                  }`}>
                    {s.icon}
                  </div>
                  <span className={`text-xs mt-2 font-medium transition-colors ${
                    i <= step ? 'text-primary-600' : 'text-slate-400'
                  }`}>
                    {s.name}
                  </span>
                </div>
                {i < steps.length - 1 && (
                  <div className={`h-1 flex-1 mx-2 transition-all rounded-full ${
                    i < step ? 'bg-primary-500' : 'bg-slate-200'
                  }`}></div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Form Content */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
          {step === 0 && renderBasicInfoStep()}
          {step === 1 && renderBagsStep()}
          {step === 2 && renderReviewStep()}

          {/* Navigation */}
          <div className="flex justify-between mt-8 pt-6 border-t border-slate-200">
            <button
              onClick={() => setStep(Math.max(0, step - 1))}
              disabled={step === 0}
              className="px-6 py-3 border-2 border-slate-300 rounded-xl text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-all"
            >
              ← Назад
            </button>

            {step < steps.length - 1 ? (
              <button
                onClick={() => setStep(step + 1)}
                disabled={!canProceed()}
                className="px-6 py-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 disabled:bg-slate-300 disabled:cursor-not-allowed font-medium transition-all shadow-lg shadow-cyan-500/30 disabled:shadow-none"
              >
                Далее →
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="px-8 py-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 disabled:bg-cyan-400 font-semibold transition-all shadow-lg shadow-cyan-500/30 flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Создание...
                  </>
                ) : (
                  'Создать отправку'
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
