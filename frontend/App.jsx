import { useState } from "react";
import axios from "axios";

function App() {
  const [merchantId, setMerchantId] = useState("");
  const [amountPaise, setAmountPaise] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const send = async () => {
    setMessage("");

    if (!merchantId || !amountPaise) {
      setMessage("Please enter merchant ID and amount.");
      return;
    }

    try {
      setLoading(true);

      const response = await axios.post(
        "http://localhost:8000/api/v1/payouts/",
        {
          merchant_id: merchantId,
          amount_paise: Number(amountPaise),
        },
        {
          headers: {
            "Idempotency-Key": crypto.randomUUID(),
          },
        }
      );

      setMessage(`Success: payout created with status "${response.data.status}"`);
      setAmountPaise("");
    } catch (error) {
      setMessage(
        error?.response?.data?.detail || "Request failed. Check backend and payload."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1 style={styles.title}>Playto Payout Test</h1>
        <p style={styles.subtitle}>Send a payout request to your Django backend.</p>

        <input
          type="text"
          placeholder="Merchant ID"
          value={merchantId}
          onChange={(e) => setMerchantId(e.target.value)}
          style={styles.input}
        />

        <input
          type="number"
          placeholder="Amount in paise"
          value={amountPaise}
          onChange={(e) => setAmountPaise(e.target.value)}
          style={styles.input}
        />

        <button onClick={send} disabled={loading} style={styles.button}>
          {loading ? "Sending..." : "Send"}
        </button>

        {message ? <p style={styles.message}>{message}</p> : null}
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "#f8fafc",
    padding: "24px",
    fontFamily: "Arial, sans-serif",
  },
  card: {
    width: "100%",
    maxWidth: "420px",
    background: "#ffffff",
    padding: "24px",
    borderRadius: "16px",
    boxShadow: "0 10px 30px rgba(0,0,0,0.08)",
  },
  title: {
    margin: "0 0 8px",
    fontSize: "28px",
    color: "#0f172a",
  },
  subtitle: {
    margin: "0 0 20px",
    color: "#475569",
    fontSize: "14px",
  },
  input: {
    width: "100%",
    padding: "12px 14px",
    marginBottom: "12px",
    borderRadius: "10px",
    border: "1px solid #cbd5e1",
    fontSize: "14px",
    boxSizing: "border-box",
  },
  button: {
    width: "100%",
    padding: "12px 14px",
    border: "none",
    borderRadius: "10px",
    background: "#0f172a",
    color: "#ffffff",
    fontSize: "15px",
    cursor: "pointer",
  },
  message: {
    marginTop: "14px",
    fontSize: "14px",
    color: "#0f172a",
  },
};

export default App;