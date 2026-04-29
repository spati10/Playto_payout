import EmptyState from "./EmptyState";
import { formatINRFromPaise } from "../utils/money";

function formatEntryLabel(type) {
  switch (type) {
    case "credit":
      return "Credit";
    case "hold":
      return "Hold";
    case "debit":
      return "Debit";
    case "release":
      return "Release";
    default:
      return type;
  }
}

function amountTone(type) {
  if (type === "credit" || type === "release") {
    return "text-emerald-700";
  }
  if (type === "hold" || type === "debit") {
    return "text-slate-900";
  }
  return "text-slate-700";
}

export default function LedgerTable({ ledger = [] }) {
  if (ledger.length === 0) {
    return (
      <EmptyState
        title="No ledger activity yet"
        description="Incoming credits, held payout amounts, debits, and releases will appear here."
      />
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr className="text-left text-sm text-slate-500">
              <th className="px-5 py-3 font-medium">Type</th>
              <th className="px-5 py-3 font-medium">Amount</th>
              <th className="px-5 py-3 font-medium">Reference</th>
              <th className="px-5 py-3 font-medium">Timestamp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white text-sm text-slate-700">
            {ledger.map((entry) => (
              <tr key={entry.id}>
                <td className="px-5 py-4 font-medium text-slate-900">
                  {formatEntryLabel(entry.entry_type)}
                </td>
                <td className={`px-5 py-4 font-medium ${amountTone(entry.entry_type)}`}>
                  {formatINRFromPaise(entry.amount_paise)}
                </td>
                <td className="px-5 py-4 text-slate-500">
                  {entry.reference_type}
                </td>
                <td className="px-5 py-4">
                  {new Date(entry.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}