import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  CheckCircle2,
  Clock,
  UserCircle,
  PackageCheck,
  Warehouse,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { shipmentService } from '../services/shipments';

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
          <div className="inline-block w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
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
              className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl"
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
          </dl>
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
        <h2 className="font-medium mb-3">Информация о пакетах</h2>
        <div className="min-w-0">
          <div className="grid grid-cols-12 text-xs">
            <div className="col-span-2 font-medium py-2 px-3 bg-slate-50">
              Пакет
            </div>
            <div className="col-span-10 font-medium py-2 px-3 bg-slate-50">
              Размеры
            </div>
            {data.shipment.bags.map((b: any) => (
              <div key={b.bag_id} className="contents">
                <div className="col-span-2 py-2 px-3 border-b">
                  {b.bag_id}
                </div>
                <div className="col-span-10 py-2 px-3 border-b">
                  {Object.entries(b.sizes).map(([k, v]) => (
                    <span
                      key={k}
                      className="inline-flex items-center rounded-full border px-2 py-0.5 mr-2 mb-1"
                    >
                      {k}-{v as number}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 3-stage status line */}
      <div className="rounded-2xl bg-white shadow-sm border border-slate-100 p-4 md:p-6 mb-6">
        <h2 className="font-medium mb-4">Статус отправки</h2>

        <div className="relative flex flex-col md:flex-row items-center md:justify-between">
          {STAGES.map((st, i) => {
            const done = statusIdx >= i;
            const Icon = st.icon;
            return (
              <div key={st.key} className="flex-1 flex flex-col items-center">
                {/* Connector line (rendered between nodes) */}
                {i > 0 && (
                  <div
                    className={classNames(
                      'absolute top-7 left-0 right-0 h-0.5',
                      statusIdx + 1 > i ? 'bg-emerald-400' : 'bg-amber-300'
                    )}
                    style={{ zIndex: 0 }}
                  />
                )}

                <motion.div
                  initial={{ scale: 0.9, opacity: 0.7 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className={classNames(
                    'relative z-10 flex items-center justify-center w-12 h-12 rounded-full ring-8',
                    done
                      ? 'bg-emerald-500 text-white ring-emerald-100'
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
                <div className="h-5 mt-1 text-xs text-emerald-600">
                  {done ? st.successLabel : ''}
                </div>
              </div>
            );
          })}
        </div>

        <p className="mt-4 text-xs text-slate-500">
          Нажимая «ПОДТВЕРДИТЬ», вы подтверждаете действие на текущем этапе.
        </p>
      </div>

      {/* Confirm bar */}
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
                ? 'bg-emerald-500 hover:bg-emerald-600 text-white'
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
    </div>
  );
}
