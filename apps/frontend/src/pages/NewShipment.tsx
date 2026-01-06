import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, ChevronDown, ChevronUp, Package, Edit2, Check, Loader2, ArrowLeft } from 'lucide-react';
import { shipmentService } from '../services/shipments';

export function NewShipment() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Form data
  const [shipmentId, setShipmentId] = useState('');
  const [supplier, setSupplier] = useState('');
  const [warehouse, setWarehouse] = useState('');
  const [routeType, setRouteType] = useState<'DIRECT' | 'VIA_FF'>('VIA_FF');
  const [bags, setBags] = useState<Array<{ bag_id: string; sizes: Record<string, number> }>>([]);

  // UI state
  const [expandedBag, setExpandedBag] = useState<string | null>(null);
  const [editingBag, setEditingBag] = useState<string | null>(null);

  const warehouses = ['Казань', 'Краснодар', 'Электросталь', 'Коледино', 'Тула', 'Невинномысск', 'Рязань', 'Новосибирск', 'Алматы', 'Котовск'];
  const sizes = ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL', '6XL'];

  const steps = [
    { name: 'Основные данные', icon: '📋' },
    { name: 'Мешки', icon: '📦' },
    { name: 'Проверка', icon: '✓' }
  ];

  const addBag = () => {
    const bagNumber = bags.length + 1;
    const newBag = {
      bag_id: `${shipmentId}-${bagNumber}`,
      sizes: {}
    };
    setBags([...bags, newBag]);
    setExpandedBag(newBag.bag_id);
    setEditingBag(newBag.bag_id);
  };

  const removeBag = (bagId: string) => {
    setBags(bags.filter(b => b.bag_id !== bagId));
  };

  const updateBagSize = (bagId: string, size: string, value: string) => {
    setBags(bags.map(bag => {
      if (bag.bag_id === bagId) {
        const newSizes = { ...bag.sizes };
        const numValue = parseInt(value) || 0;
        if (numValue === 0 || value === '') {
          delete newSizes[size];
        } else {
          newSizes[size] = numValue;
        }
        return { ...bag, sizes: newSizes };
      }
      return bag;
    }));
  };

  const calculateBagTotal = (bag: { sizes: Record<string, number> }) => {
    return Object.values(bag.sizes).reduce((sum, qty) => sum + (qty || 0), 0);
  };

  const calculateTotal = () => {
    return bags.reduce((sum, bag) => sum + calculateBagTotal(bag), 0);
  };

  const canProceed = () => {
    if (step === 0) return shipmentId.trim() !== '' && supplier.trim() !== '' && warehouse !== '';
    if (step === 1) return bags.length > 0 && calculateTotal() > 0;
    return true;
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');

    try {
      await shipmentService.createShipment({
        id: shipmentId,
        supplier,
        warehouse,
        route_type: routeType,
        bags
      });

      navigate('/shipments');
    } catch (e: any) {
      setError(e.message || 'Ошибка при создании отправки');
      setLoading(false);
    }
  };

  const renderBasicInfoStep = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-900">Основные данные</h2>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            ID Отправки *
          </label>
          <input
            type="text"
            value={shipmentId}
            onChange={(e) => setShipmentId(e.target.value)}
            placeholder="Например: SHIP-001"
            className="w-full p-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Поставщик *
          </label>
          <input
            type="text"
            value={supplier}
            onChange={(e) => setSupplier(e.target.value)}
            placeholder="Название поставщика"
            className="w-full p-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Склад назначения *
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {warehouses.map(wh => (
              <button
                key={wh}
                onClick={() => setWarehouse(wh)}
                className={`p-3 rounded-xl border-2 transition-all ${
                  warehouse === wh
                    ? 'border-emerald-500 bg-emerald-50 text-emerald-700 font-medium'
                    : 'border-slate-200 hover:border-slate-300 text-slate-700'
                }`}
              >
                {wh}
              </button>
            ))}
          </div>
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
                  ? 'border-emerald-500 bg-emerald-50 text-emerald-700 font-medium'
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
                  ? 'border-emerald-500 bg-emerald-50 text-emerald-700 font-medium'
                  : 'border-slate-200 hover:border-slate-300 text-slate-700'
              }`}
            >
              <div className="text-sm font-semibold mb-1">Прямая доставка</div>
              <div className="text-xs opacity-75">Поставщик → Склад</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderBagsStep = () => {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-slate-900">Мешки</h2>
          <div className="text-sm text-slate-600">
            <span className="font-semibold">{calculateTotal()}</span> вещей •
            <span className="font-semibold ml-2">{bags.length}</span> мешков
          </div>
        </div>

        {/* Add Bag Button */}
        {shipmentId && (
          <button
            onClick={addBag}
            className="w-full p-4 bg-emerald-50 border-2 border-dashed border-emerald-300 rounded-xl text-emerald-600 hover:bg-emerald-100 hover:border-emerald-400 transition-all flex items-center justify-center gap-2 font-medium"
          >
            <Plus size={20} /> Добавить мешок
          </button>
        )}

        {!shipmentId && (
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-700 text-sm">
            Сначала укажите ID отправки на предыдущем шаге
          </div>
        )}

        {/* Bags List */}
        <div className="space-y-3">
          {bags.map((bag) => (
            <div key={bag.bag_id} className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm">
              <button
                onClick={() => setExpandedBag(expandedBag === bag.bag_id ? null : bag.bag_id)}
                className="w-full p-4 hover:bg-slate-50 flex items-center justify-between transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Package className="text-emerald-500 flex-shrink-0" size={20} />
                  <div className="text-left">
                    <span className="font-mono text-sm font-semibold text-slate-900 block">{bag.bag_id}</span>
                    <span className="text-xs text-slate-500">
                      {calculateBagTotal(bag)} вещей
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditingBag(editingBag === bag.bag_id ? null : bag.bag_id);
                    }}
                    className="p-2 hover:bg-emerald-100 rounded-lg transition-colors"
                    title={editingBag === bag.bag_id ? 'Готово' : 'Редактировать'}
                  >
                    {editingBag === bag.bag_id ? (
                      <Check size={16} className="text-emerald-600" />
                    ) : (
                      <Edit2 size={16} className="text-emerald-600" />
                    )}
                  </button>
                  {bags.length > 1 && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        removeBag(bag.bag_id);
                      }}
                      className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                      title="Удалить мешок"
                    >
                      <Trash2 size={16} className="text-red-600" />
                    </button>
                  )}
                  {expandedBag === bag.bag_id ? (
                    <ChevronUp size={20} className="text-slate-400" />
                  ) : (
                    <ChevronDown size={20} className="text-slate-400" />
                  )}
                </div>
              </button>

              {expandedBag === bag.bag_id && editingBag === bag.bag_id && (
                <div className="p-4 bg-slate-50 border-t border-slate-200">
                  <div className="grid grid-cols-3 sm:grid-cols-5 gap-3">
                    {sizes.map(size => (
                      <div key={size} className="flex flex-col">
                        <label className="text-xs font-medium text-slate-600 mb-1">{size}</label>
                        <input
                          type="number"
                          min="0"
                          value={bag.sizes[size] || ''}
                          onChange={(e) => updateBagSize(bag.bag_id, size, e.target.value)}
                          className="p-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                          placeholder="0"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {expandedBag === bag.bag_id && editingBag !== bag.bag_id && Object.keys(bag.sizes).length > 0 && (
                <div className="p-4 bg-slate-50 border-t border-slate-200 flex flex-wrap gap-2">
                  {Object.entries(bag.sizes).map(([size, qty]) => (
                    qty > 0 && (
                      <span key={size} className="px-3 py-1.5 bg-emerald-100 text-emerald-700 rounded-lg text-sm font-medium">
                        {size}: {qty}
                      </span>
                    )
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {bags.length === 0 && shipmentId && (
          <div className="p-12 text-center border-2 border-dashed border-slate-200 rounded-xl">
            <Package className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">Нет мешков</h3>
            <p className="text-slate-600 mb-6">Добавьте первый мешок в отправку</p>
          </div>
        )}
      </div>
    );
  };

  const renderReviewStep = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-900">Проверка отправки</h2>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
          {error}
        </div>
      )}

      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6 space-y-3">
        <div className="flex justify-between py-2">
          <span className="font-medium text-slate-700">ID Отправки:</span>
          <span className="font-mono font-semibold text-emerald-600">{shipmentId}</span>
        </div>
        <div className="flex justify-between py-2 border-t border-emerald-200">
          <span className="font-medium text-slate-700">Поставщик:</span>
          <span className="font-semibold text-slate-900">{supplier}</span>
        </div>
        <div className="flex justify-between py-2 border-t border-emerald-200">
          <span className="font-medium text-slate-700">Склад:</span>
          <span className="font-semibold text-slate-900">{warehouse}</span>
        </div>
        <div className="flex justify-between py-2 border-t border-emerald-200">
          <span className="font-medium text-slate-700">Маршрут:</span>
          <span className="font-semibold text-slate-900">
            {routeType === 'VIA_FF' ? 'Через Фулфилмент' : 'Прямая доставка'}
          </span>
        </div>
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded-xl p-6">
        <div className="grid grid-cols-2 gap-6 text-center">
          <div>
            <div className="text-4xl font-bold text-emerald-600 mb-1">{bags.length}</div>
            <div className="text-sm text-slate-600 font-medium">Мешков</div>
          </div>
          <div>
            <div className="text-4xl font-bold text-emerald-600 mb-1">{calculateTotal()}</div>
            <div className="text-sm text-slate-600 font-medium">Всего вещей</div>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="font-semibold text-slate-800 text-lg">Детальная информация:</h3>
        {bags.map(bag => (
          <div key={bag.bag_id} className="border border-slate-200 rounded-xl p-4 bg-white">
            <div className="font-mono text-sm font-semibold text-emerald-600 mb-2">{bag.bag_id}</div>
            <div className="flex flex-wrap gap-2">
              {Object.entries(bag.sizes).map(([size, qty]) => (
                qty > 0 && (
                  <span key={size} className="px-2.5 py-1 bg-slate-100 text-slate-700 rounded text-sm">
                    {size}: {qty}
                  </span>
                )
              ))}
            </div>
            <div className="mt-2 text-sm text-slate-600">
              Всего: <span className="font-semibold">{calculateBagTotal(bag)}</span> вещей
            </div>
          </div>
        ))}
      </div>
    </div>
  );

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
                    i <= step ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/30' : 'bg-slate-200 text-slate-500'
                  }`}>
                    {s.icon}
                  </div>
                  <span className={`text-xs mt-2 font-medium transition-colors ${
                    i <= step ? 'text-emerald-600' : 'text-slate-400'
                  }`}>
                    {s.name}
                  </span>
                </div>
                {i < steps.length - 1 && (
                  <div className={`h-1 flex-1 mx-2 transition-all rounded-full ${
                    i < step ? 'bg-emerald-500' : 'bg-slate-200'
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
                className="px-6 py-3 bg-emerald-500 text-white rounded-xl hover:bg-emerald-600 disabled:bg-slate-300 disabled:cursor-not-allowed font-medium transition-all shadow-lg shadow-emerald-500/30 disabled:shadow-none"
              >
                Далее →
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="px-8 py-3 bg-emerald-500 text-white rounded-xl hover:bg-emerald-600 disabled:bg-emerald-400 font-semibold transition-all shadow-lg shadow-emerald-500/30 flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Создание...
                  </>
                ) : (
                  <>
                    <Check className="w-5 h-5" />
                    Создать отправку
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
