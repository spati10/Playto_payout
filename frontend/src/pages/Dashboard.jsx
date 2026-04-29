import { useEffect, useState } from "react";
import { api } from "../api/client";
import BalanceCard from "../components/BalanceCard";
import LedgerTable from "../components/LedgerTable";
import PayoutForm from "../components/PayoutForm";
import PayoutTable from "../components/PayoutTable";

export default function Dashboard() {
  const merchantId = import.meta.env.VITE_MERCHANT_ID;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard() {
    if (!merchantId || merchantId === "your-real-merchant-uuid-here") {
      setError("VITE_MERCHANT_ID is missing or still using the placeholder value.");
      setLoading(false);
      return;
    }

    try {
      setError("");
      const response = await api.get(`/merchants/${merchantId}/dashboard/`);
      setData(response.data);
    } catch (err) {
      if (err.response) {
        setError(`Backend responded with ${err.response.status}. Check the dashboard API and merchant UUID.`);
      } else if (err.request) {
        setError("Cannot reach backend at http://127.0.0.1:8000. Start Django server first.");
      } else {
        setError("Unexpected frontend error while loading dashboard.");
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let timer;

    if (merchantId && merchantId !== "your-real-merchant-uuid-here") {
      loadDashboard();
      timer = setInterval(loadDashboard, 5000);
    } else {
      setError("VITE_MERCHANT_ID is missing or still using the placeholder value.");
      setLoading(false);
    }

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [merchantId]);

  if (loading) {
    return <div className="p-8 text-slate-600">Loading dashboard...</div>;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 p-8">
        <div className="mx-auto max-w-3xl rounded-2xl border border-red-200 bg-white p-6 shadow-sm">
          <h1 className="text-xl font-semibold text-slate-900">Dashboard unavailable</h1>
          <p className="mt-2 text-sm text-red-600">{error}</p>
          <div className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-700">
            <p>Check these:</p>
            <ul className="mt-2 list-disc pl-5">
              <li>Django is running on port 8000.</li>
              <li>VITE_API_BASE_URL is correct.</li>
              <li>VITE_MERCHANT_ID contains a real seeded merchant UUID.</li>
              <li>The backend returns merchant, bank_accounts, payouts, and ledger fields.</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  if (!data || !data.merchant) {
    return <div className="p-8 text-slate-600">No dashboard data found.</div>;
  }

  const ledger = data?.ledger ?? [];

  const debitEntries = ledger.filter(
    (entry) => entry.entry_type === "debit" || entry.entry_type === "hold"
  );

  const creditEntries = ledger.filter(
    (entry) => entry.entry_type === "credit" || entry.entry_type === "release"
  );

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8 md:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <p className="text-sm text-slate-500">Merchant Dashboard</p>
          <h1 className="text-3xl font-bold text-slate-900">{data.merchant.name}</h1>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <BalanceCard
            label="Available balance"
            amount={data.available_balance_paise ?? 0}
            tone="text-emerald-600"
          />
          <BalanceCard
            label="Held balance"
            amount={data.held_balance_paise ?? 0}
            tone="text-amber-600"
          />
          <BalanceCard
            label="Total credits"
            amount={data.total_credits_paise ?? 0}
          />
          <BalanceCard
            label="Total debits"
            amount={data.total_debits_paise ?? 0}
            tone="text-rose-600"
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div>
            <PayoutForm
              merchantId={data.merchant.id}
              bankAccounts={data.bank_accounts ?? []}
              onSuccess={loadDashboard}
            />
          </div>
          <div className="lg:col-span-2">
            <PayoutTable payouts={data.payouts ?? []} />
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Recent Debits</h2>
              <span className="text-xs text-slate-500">Live · </span>
            </div>

            {debitEntries.length === 0 ? (
              <p className="mt-4 text-sm text-slate-500">No debit activity yet.</p>
            ) : (
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-slate-500">
                      <th className="py-3 pr-4">Type</th>
                      <th className="py-3 pr-4">Amount</th>
                      <th className="py-3 pr-4">Reference</th>
                      <th className="py-3">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {debitEntries.map((entry) => (
                      <tr key={entry.id} className="border-b last:border-b-0">
                        <td className="py-3 pr-4">
                          <span className="rounded-full bg-rose-50 px-2 py-1 text-xs font-medium uppercase text-rose-700">
                            {entry.entry_type}
                          </span>
                        </td>
                        <td className="py-3 pr-4 font-medium text-slate-900">
                          ₹{(entry.amount_paise / 100).toFixed(2)}
                        </td>
                        <td className="py-3 pr-4 text-slate-600">
                          {entry.reference_type || "—"}
                        </td>
                        <td className="py-3 text-slate-600">
                          {new Date(entry.created_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Recent credits</h2>
              <span className="text-xs text-slate-500">Live · </span>
            </div>

            {creditEntries.length === 0 ? (
              <p className="mt-4 text-sm text-slate-500">No credit activity yet.</p>
            ) : (
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-slate-500">
                      <th className="py-3 pr-4">Type</th>
                      <th className="py-3 pr-4">Amount</th>
                      <th className="py-3 pr-4">Reference</th>
                      <th className="py-3">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {creditEntries.map((entry) => (
                      <tr key={entry.id} className="border-b last:border-b-0">
                        <td className="py-3 pr-4">
                          <span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-medium uppercase text-emerald-700">
                            {entry.entry_type}
                          </span>
                        </td>
                        <td className="py-3 pr-4 font-medium text-slate-900">
                          ₹{(entry.amount_paise / 100).toFixed(2)}
                        </td>
                        <td className="py-3 pr-4 text-slate-600">
                          {entry.reference_type || "—"}
                        </td>
                        <td className="py-3 text-slate-600">
                          {new Date(entry.created_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>

        <LedgerTable ledger={data.ledger ?? []} />
      </div>
    </div>
  );
}