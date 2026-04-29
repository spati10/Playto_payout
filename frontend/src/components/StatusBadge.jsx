const STATUS_STYLES = {
  pending: "bg-amber-50 text-amber-700 ring-amber-200",
  processing: "bg-sky-50 text-sky-700 ring-sky-200",
  completed: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  failed: "bg-rose-50 text-rose-700 ring-rose-200",
};

export default function StatusBadge({ status }) {
  const normalized = String(status || "").toLowerCase();
  const classes =
    STATUS_STYLES[normalized] || "bg-slate-100 text-slate-700 ring-slate-200";

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium capitalize ring-1 ring-inset ${classes}`}
    >
      {normalized || "unknown"}
    </span>
  );
}