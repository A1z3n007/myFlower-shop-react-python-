import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Api } from "../data/api.js";

export default function OrdersPage() {
  const [email, setEmail] = useState(() => localStorage.getItem("user.email") || "");
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const load = async (e) => {
    if (e) e.preventDefault();
    try {
      setLoading(true);
      setErr("");
      localStorage.setItem("user.email", email);
      const data = await Api.getOrders({ email });
      setOrders(data);
    } catch (error) {
      setErr(error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (email) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <section>
      <h1 className="page-title">Мои заказы</h1>
      <form className="filters" onSubmit={load}>
        <input
          className="input"
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <button className="btn">Показать</button>
      </form>

      {loading && <div className="muted">Загружаем историю...</div>}
      {err && <div className="err">{err}</div>}

      {!loading && !err && (
        orders.length === 0 ? (
          <div className="empty">Заказов пока нет.</div>
        ) : (
          <div className="order-list">
            {orders.map((o) => (
              <div key={o.id} className="order-card">
                <div className="order-head">
                  <div><b>Заказ #{o.id}</b> — <span className={`st-badge st-${o.status}`}>{o.status}</span></div>
                  <div className="muted">{new Date(o.created_at).toLocaleString()}</div>
                  <div className="order-sum">Итого: <b>{o.total} ₸</b></div>
                </div>
                <ul className="order-items">
                  {o.items_info?.slice(0, 3).map((oi) => (
                    <li key={oi.id}>
                      <img src={oi.product.image_url} alt="" loading="lazy" />
                      <div className="s-title">{oi.product.name}</div>
                      <div className="s-qty">× {oi.qty}</div>
                      <div className="s-price">{oi.price_at_purchase * oi.qty} ₸</div>
                    </li>
                  ))}
                </ul>
                <div style={{ marginTop: 10 }}>
                  <Link className="btn btn-ghost" to={`/orders/${o.id}`}>Подробнее</Link>
                </div>
              </div>
            ))}
          </div>
        )
      )}
    </section>
  );
}
