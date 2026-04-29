import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function PayoutForm({
  merchantId,
  bankAccounts = [],
  onPayoutCreated,
}) {
  const [bankAccountId, setBankAccountId] = useState("");
  const [amount, setAmount] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (bankAccounts.length > 0 && !bankAccountId) {
      setBankAccountId(bankAccounts[0].id);
    }
  }, [bankAccounts, bankAccountId]);

  async function handleSubmit(event) {
    event.preventDefault();

    setMessage("");
    setError("");

    const numericAmount = Number(amount);
    const amountInPaise = Math.round(numericAmount * 100);

    if (!amount || Number.isNaN(numericAmount) || amountInPaise <= 0) {
      setError("Enter a valid payout amount");
      return;
    }

    if (!bankAccountId) {
      setError("Select a bank account");
      return;
    }

    setSubmitting(true);

    try {
      const response = await api.post(
        "/payouts/",
        {
          merchant_id: merchantId,
          bank_account_id: bankAccountId,
          amount_paise: amountInPaise,
        },
        {
          headers: {
            "Idempotency-Key": crypto.randomUUID(),
          },
        }
      );

      setMessage(`Payout created: ${response.data.id.slice(0, 8)}`);
      setAmount("");
      onPayoutCreated?.();
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Could not create payout"
      );
    } finally {
      setSubmitting(false);
    }
  }

  const hasBankAccounts = bankAccounts.length > 0;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-slate-900">Request payout</h3>
        <p className="mt-1 text-sm text-slate-500">
          Create a payout request against the currently available balance.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="payout-amount"
            className="mb-2 block text-sm font-medium text-slate-700"
          >
            Amount (INR)
          </label>
          <input
            id="payout-amount"
            type="number"
            min="1"
            
            placeholder="500"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
          />
        </div>

        <div>
          <label
            htmlFor="bank-account"
            className="mb-2 block text-sm font-medium text-slate-700"
          >
            Bank Account
          </label>
          <select
            id="bank-account"
            value={bankAccountId}
            onChange={(e) => setBankAccountId(e.target.value)}
            disabled={!hasBankAccounts}
            className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200 disabled:cursor-not-allowed disabled:bg-slate-100"
          >
            {hasBankAccounts ? (
              bankAccounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.bank_name} • {account.masked_account_number}
                </option>
              ))
            ) : (
              <option value="">No active bank accounts available</option>
            )}
          </select>
        </div>

        {message ? (
          <div className="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            {message}
          </div>
        ) : null}

        {error ? (
          <div className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        <button
          type="submit"
          disabled={submitting || !hasBankAccounts}
          className="w-full rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? "Submitting..." : "Create payout"}
        </button>
      </form>
    </div>
  );
}