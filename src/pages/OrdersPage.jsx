import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Api } from "../data/api.js";

export default function OrdersPage() {
  const isAuth = !!localStorage.getItem("jwt");
  const userEmail = localStorage.getItem("user_email") || "";
  const [email, setEmail] = useState(() => localStorage.getItem("user.email") || "");
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const fetchOrders = async (lookupEmail = email) => {
    try {
      setLoading(true);
      setErr("");
      if (!isAuth) {
        localStorage.setItem("user.email", lookupEmail);
      }
      const params = isAuth ? { mine: true } : { email: lookupEmail };
      const data = await Api.getOrders(params);
      setOrders(data);
    } catch (error) {
      setErr(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchOrders();
  };

  useEffect(() => {
    if (isAuth) {
      fetchOrders();
    } else if (email) {
      fetchOrders(email);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuth]);

  return (
    <section>
      <h1 className="page-title">Мои заказы</h1>

      {isAuth ? (
        <div className="muted" style={{ marginBottom: 12 }}>
          Вы вошли как {userEmail || "гость"}. Показаны только ваши заказы.
        </div>
      ) : (
        <form className="filters" onSubmit={handleSubmit}>
          <input
            className="input"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <button className="btn">Показать заказы</button>
        </form>
      )}

      {loading && <div className="muted">Загружаем историю заказов…</div>}
      {err && <div className="err">{err}</div>}

      {!loading && !err && (
        orders.length === 0 ? (
          <div className="empty">Заказов пока нет.</div>
        ) : (
          <div className="order-list">
            {orders.map((o) => (
              <div key={o.id} className="order-card">
                <div className="order-head">
                  <div>
                    <b>Заказ #{o.id}</b> —{" "}
                    <span className={`st-badge st-${o.status}`}>{o.status}</span>
                  </div>
                  <div className="muted">{new Date(o.created_at).toLocaleString()}</div>
                  <div className="order-sum">Сумма: <b>{o.total} ₸</b></div>
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
                  <Link className="btn btn-ghost" to={`/orders/${o.id}`}>
                    Подробнее
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )
      )}
    </section>
  );
}
