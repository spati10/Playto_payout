import StatusBadge from "./StatusBadge";
import EmptyState from "./EmptyState";
import { formatINRFromPaise } from "../utils/money";

export default function PayoutTable({ payouts = [] }) {
  if (payouts.length === 0) {
    return (
      <EmptyState
        title="No payouts yet"
        description="Create your first payout request to see its status appear here."
      />
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr className="text-left text-sm text-slate-500">
              <th className="px-5 py-3 font-medium">Payout</th>
              <th className="px-5 py-3 font-medium">Amount</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium">Attempts</th>
              <th className="px-5 py-3 font-medium">Created</th>
              <th className="px-5 py-3 font-medium">Failure reason</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white text-sm text-slate-700">
            {payouts.map((payout) => (
              <tr key={payout.id}>
                <td className="px-5 py-4 font-medium text-slate-900">
                  {payout.id.slice(0, 8)}
                </td>
                <td className="px-5 py-4">
                  {formatINRFromPaise(payout.amount_paise)}
                </td>
                <td className="px-5 py-4">
                  <StatusBadge status={payout.status} />
                </td>
                <td className="px-5 py-4">{payout.attempts}</td>
                <td className="px-5 py-4">
                  {new Date(payout.created_at).toLocaleString()}
                </td>
                <td className="px-5 py-4 text-slate-500">
                  {payout.failure_reason || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}