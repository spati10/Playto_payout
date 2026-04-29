import { formatINRFromPaise } from "../utils/money";

export default function BalanceCard({
  label,
  amount,
  tone = "text-slate-900",
  helpText = "",
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <div className="mt-3 flex items-end justify-between gap-3">
        <h3 className={`text-2xl font-semibold tracking-tight ${tone}`}>
          {formatINRFromPaise(amount)}
        </h3>
      </div>
      {helpText ? (
        <p className="mt-2 text-xs text-slate-500">{helpText}</p>
      ) : null}
    </div>
  );
}