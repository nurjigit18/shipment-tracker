import React, { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, Clock, UserCircle, PackageCheck, Warehouse } from "lucide-react";

// ---------- Utilities ----------
const ROLES: Record<string, string> = {
  supplier: "поставщик",
  ff: "фуллфилмент",
  driver: "водитель",
  warehouse: "склад",
};

const STAGES = [
  { key: "SENT_FROM_FACTORY" as const, label: "Поставщик", successLabel: "Отправлено", icon: CheckCircle2 },
  { key: "SHIPPED_FROM_FF" as const, label: "Фулфилмент", successLabel: "Отправлено", icon: PackageCheck },
  { key: "DELIVERED" as const, label: "Склад (водитель)", successLabel: "Доставлено", icon: Warehouse },
];

type Status = typeof STAGES[number]["key"] | null;

// Порядок статусов для расчёта прогресса
const ORDER: Record<string, number> = {
  NONE: -1,
  SENT_FROM_FACTORY: 0,
  SHIPPED_FROM_FF: 1,
  DELIVERED: 2,
};

// Русские подписи для текущего статуса
const STATUS_RU: Record<string, string> = {
  SENT_FROM_FACTORY: "Отправлено от Поставщика",
  SHIPPED_FROM_FF: "Отправлено из Фулфилмента",
  DELIVERED: "Доставлено",
};

function classNames(...xs: Array<string | false | null | undefined>) {
  return xs.filter(Boolean).join(" ");
}

function useQuery() {
  return useMemo(() => new URLSearchParams(window.location.search), []);
}

// ---------- Auth (very light mock; replace with your real flow) ----------
function useAuth() {
  const [user, setUser] = useState<null | { username: string; role: string }>(null);

  useEffect(() => {
    const cached = localStorage.getItem("ne_auth");
    if (cached) {
      try { setUser(JSON.parse(cached)); } catch {}
    }
  }, []);

  const login = async ({ username, password, remember, role }: { username: string; password: string; remember: boolean; role: string; }) => {
    // TODO: call your /api/auth/login; role is selected for demo only
    // const res = await fetch("/api/auth/login", { method: "POST", ... })
    const u = { username, role };
    setUser(u);
    if (remember) localStorage.setItem("ne_auth", JSON.stringify(u));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("ne_auth");
  };

  return { user, login, logout };
}

// ---------- Sample payload (used as fallback when API not wired yet) ----------
const SAMPLE_SHIPMENT = {
  shipment: {
    id: "S-2025-00123",
    supplier: "Нарселя",
    warehouse: "Казань",
    route_type: "VIA_FF", // or DIRECT
    current_status: null as Status, // null | "SENT_FROM_FACTORY" | "SHIPPED_FROM_FF" | "DELIVERED"
    bags: [
      { bag_id: "B-1", sizes: { S: 10, M: 20, L: 15 } },
      { bag_id: "B-2", sizes: { M: 12, XL: 4 } },
      { bag_id: "B-3", sizes: { S: 5, M: 7, L: 8 } },
    ],
    totals: { bags: 3, pieces: 81 },
  },
  events: [] as Array<any>,
};

// ---------- Main App ----------
export default function App() {
  const { user, login, logout } = useAuth();
  const qp = useQuery();
  const sidFromQuery = qp.get("sid") || qp.get("s") || qp.get("shipment") || undefined;
  const [sid] = useState<string>(sidFromQuery || "S-2025-00123");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<typeof SAMPLE_SHIPMENT>(SAMPLE_SHIPMENT);

  useEffect(() => {
    let ignore = false;
    const load = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/shipments/${encodeURIComponent(sid)}`);
        if (!res.ok) throw new Error("HTTP " + res.status);
        const json = await res.json();
        if (!ignore) setData(json);
      } catch (e) {
        // Fallback to sample if API not ready
        if (!ignore) setData((s) => ({ ...SAMPLE_SHIPMENT, shipment: { ...SAMPLE_SHIPMENT.shipment, id: sid } }));
      } finally {
        if (!ignore) setLoading(false);
      }
    };
    if (sid) load();
    return () => { ignore = true; };
  }, [sid]);

  return (
    <div className="min-h-screen w-screen bg-neutral-50 text-slate-800">
      {!user ? (
        <AuthScreen onLogin={login} defaultUsername="" />
      ) : (
        <ShipmentScreen
          user={user}
          onLogout={logout}
          data={data}
          setData={setData}
          loading={loading}
        />
      )}
    </div>
  );
}

// ---------- Screens ----------
function AuthScreen({ onLogin, defaultUsername }: { onLogin: Function; defaultUsername: string }) {
  const [username, setUsername] = useState(defaultUsername);
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [role, setRole] = useState("supplier");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onLogin({ username, password, remember, role });
  };

  return (
    <div className="flex items-center justify-center min-h-screen px-4">
      <div className="w-full max-w-[480px] mx-auto rounded-2xl bg-white shadow-xl p-4 sm:p-8">
        <h1 className="text-2xl font-semibold tracking-tight mb-6 text-center">Nova Eris Tracking</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm mb-1">Логин</label>
            <input
              className="w-full rounded-xl border border-slate-200 px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-400"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Пароль</label>
            <input
              type="password"
              className="w-full rounded-xl border border-slate-200 px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-400"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>

          <div className="flex items-center justify-between text-sm">
            <label className="inline-flex items-center gap-2 select-none">
              <input type="checkbox" className="accent-emerald-500" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
              Запомнить меня
            </label>
            <a href="#" className="text-emerald-600 hover:underline">Забыли пароль</a>
          </div>

          <button type="submit" className="w-full rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white py-2.5 font-medium shadow">
            Войти
          </button>
        </form>
      </div>
    </div>
  );
}

function ShipmentScreen({ user, onLogout, data, setData, loading }: { user: { username: string; role: string }; onLogout: () => void; data: typeof SAMPLE_SHIPMENT; setData: Function; loading: boolean; }) {
  const statusIdx = ORDER[(data.shipment.current_status ?? "NONE") as string];

  const nextAction = useMemo<Status>(() => {
    if (statusIdx < 0) return "SENT_FROM_FACTORY";
    if (statusIdx === 0) return "SHIPPED_FROM_FF";
    if (statusIdx === 1) return "DELIVERED";
    return null;
  }, [statusIdx]);

  const roleAllows = (action: Status) => {
    if (!action) return false;
    if (action === "SENT_FROM_FACTORY") return user.role === "supplier" || user.role === "admin";
    if (action === "SHIPPED_FROM_FF") return user.role === "ff" || user.role === "admin";
    if (action === "DELIVERED") return ["driver", "warehouse", "admin"].includes(user.role);
    return false;
  };

  const canConfirm = roleAllows(nextAction);

  const doConfirm = async () => {
    if (!nextAction) return;
    try {
      const res = await fetch(`/api/shipments/${encodeURIComponent(data.shipment.id)}/events`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": (crypto as any).randomUUID ? crypto.randomUUID() : String(Date.now()),
        },
        body: JSON.stringify({ action: nextAction }),
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      // optimistic local update for demo
      setData({ ...data, shipment: { ...data.shipment, current_status: nextAction } });
    } catch (e) {
      // fallback: local update for demo when API is not present
      setData({ ...data, shipment: { ...data.shipment, current_status: nextAction } });
    }
  };

  return (  
    <div className="mx-auto w-full max-w-full sm:max-w-xl md:max-w-3xl px-2 sm:px-4 md:px-6 py-2 sm:py-4 md:py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div className="">
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight">Nova Eris Tracking</h1>
          <p className="text-xs sm:text-sm text-slate-500">Статус отправки и подтверждение</p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3 w-full sm:w-auto">
          <div className="text-left sm:text-right flex-1 sm:flex-none">
            <div className="text-xs sm:text-sm font-medium">{user.username || "user"} <span className="text-slate-500">({ROLES[user.role] || user.role})</span></div>
            <div className="text-xs text-slate-500">Отправка: <span className="font-mono">{data.shipment.id}</span></div>
          </div>
          <UserCircle className="w-7 h-7 sm:w-8 sm:h-8 text-slate-400 flex-shrink-0" />
          <button onClick={onLogout} className="text-xs rounded-lg border px-2 sm:px-2.5 py-1 hover:bg-slate-50 flex-shrink-0">Выйти</button>
        </div>
      </div>

      {/* Shipment info + summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 sm:gap-4 mb-4 sm:mb-6">
        <div className="rounded-2xl bg-white shadow-sm border border-slate-100 p-5">
          <h2 className="font-medium mb-3">Информация об отправке</h2>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <div className="col-span-1"><dt className="text-slate-500">Поставщик:</dt><dd className="font-medium">{data.shipment.supplier}</dd></div>
            <div className="col-span-1"><dt className="text-slate-500">Склад:</dt><dd className="font-medium">{data.shipment.warehouse}</dd></div>
            <div className="col-span-1"><dt className="text-slate-500">ID отправки:</dt><dd className="font-mono">{data.shipment.id}</dd></div>
            <div className="col-span-1"><dt className="text-slate-500">Маршрут:</dt><dd className="font-medium">{data.shipment.route_type === "DIRECT" ? "Прямой" : "Через ФФ"}</dd></div>
          </dl>
        </div>
        <div className="rounded-2xl bg-white shadow-sm border border-slate-100 p-5">
          <h2 className="font-medium mb-3">Сводки</h2>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <div className="col-span-1"><dt className="text-slate-500">Количество пакетов:</dt><dd className="font-medium">{data.shipment.totals?.bags ?? "—"}</dd></div>
            <div className="col-span-1"><dt className="text-slate-500">Общее количество (шт):</dt><dd className="font-medium">{data.shipment.totals?.pieces ?? "—"}</dd></div>
          </dl>
        </div>
      </div>

      {/* Bags strip */}
      <div className="rounded-2xl bg-white shadow-sm border border-slate-100 p-4 md:p-5 mb-6 overflow-x-auto">
        <h2 className="font-medium mb-3">Информация о пакетах</h2>
        <div className="min-w-0">
          <div className="grid grid-cols-12 text-xs">
            <div className="col-span-2 font-medium py-2 px-3 bg-slate-50">Пакет</div>
            <div className="col-span-10 font-medium py-2 px-3 bg-slate-50">Размеры</div>
            {data.shipment.bags.map((b: any) => (
              <React.Fragment key={b.bag_id}>
                <div className="col-span-2 py-2 px-3 border-b">{b.bag_id}</div>
                <div className="col-span-10 py-2 px-3 border-b">
                  {Object.entries(b.sizes).map(([k, v]) => (
                    <span key={k} className="inline-flex items-center rounded-full border px-2 py-0.5 mr-2 mb-1">{k}-{v as number}</span>
                  ))}
                </div>
              </React.Fragment>
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
                      "absolute top-7 left-0 right-0 h-0.5",
                      statusIdx + 1 > i ? "bg-emerald-400" : "bg-amber-300"
                    )}
                    style={{ zIndex: 0 }}
                  />
                )}

                <motion.div
                  initial={{ scale: 0.9, opacity: 0.7 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className={classNames(
                    "relative z-10 flex items-center justify-center w-12 h-12 rounded-full ring-8",
                    done ? "bg-emerald-500 text-white ring-emerald-100" : "bg-amber-300 text-white ring-amber-100"
                  )}
                >
                  {done ? <Icon className="w-6 h-6" /> : <Clock className="w-6 h-6" />}
                </motion.div>
                <div className="mt-2 text-sm font-medium text-center">{st.label}</div>
                <div className="h-5 mt-1 text-xs text-emerald-600">{done ? st.successLabel : ""}</div>
              </div>
            );
          })}
        </div>

        <p className="mt-4 text-xs text-slate-500">
          Нажимая «ПОДТВЕРДИТЬ», вы подтверждаете действие на текущем этапе.
        </p>
      </div>

      {/* Confirm bar (без поля ввода SID по требованию) */}
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm text-slate-500 flex items-center gap-2">
          <span className="font-medium">Текущий статус:</span>
          <span>{data.shipment.current_status ? STATUS_RU[data.shipment.current_status] : "—"}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={doConfirm}
            disabled={!canConfirm || loading || !nextAction}
            className={classNames(
              "rounded-2xl px-3 py-2 sm:px-6 sm:py-3 font-semibold tracking-wide shadow",
              canConfirm ? "bg-emerald-500 hover:bg-emerald-600 text-white" : "bg-slate-200 text-slate-500 cursor-not-allowed"
            )}
            title={!nextAction ? "Статус завершён" : !canConfirm ? "Недостаточно прав для подтверждения" : "Подтвердить"}
          >
            ПОДТВЕРДИТЬ
          </button>
        </div>
      </div>
    </div>
  );
}
