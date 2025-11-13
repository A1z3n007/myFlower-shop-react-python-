import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Api } from "../data/api.js";
import { useUi } from "../state/UIContext.jsx";

const STATUS_LABELS = {
  created: "Создан",
  processing: "Готовим",
  delivering: "Доставка",
  completed: "Завершён",
  canceled: "Отменён",
};

export default function OrderDetailsPage() {
  const { id } = useParams();
  const { pushToast } = useUi();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [form, setForm] = useState({
    address: "",
    slot: "",
    comment: "",
  });

  const load = async () => {
    try {
      setLoading(true);
      const data = await Api.getOrder(id);
      setOrder(data);
      setForm((prev) => ({
        ...prev,
        address: data.delivery_address || data.address,
      }));
      setErr("");
    } catch (error) {
      setErr(error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const requestDelivery = async (e) => {
    e.preventDefault();
    try {
      const updated = await Api.requestDelivery(order.id, {
        delivery_address: form.address,
        delivery_comment: form.comment,
      });
      setOrder(updated);
      pushToast("Доставка назначена");
    } catch (error) {
      pushToast("Не удалось обновить доставку");
    }
  };

  if (loading) return <div className="muted">Загружаем...</div>;
  if (err) return <div className="err">{err}</div>;
  if (!order) return <div className="muted">Заказ не найден</div>;

  const events = order.events || [];

  return (
    <section className="order-details">
      <header className="order-top">
        <div>
          <h1>Заказ #{order.id}</h1>
          <p className="muted">{new Date(order.created_at).toLocaleString()}</p>
        </div>
        <div className="chips">
          <span className={`st-badge st-${order.status}`}>{STATUS_LABELS[order.status] || order.status}</span>
          <span className={`dl-badge dl-${order.delivery_status}`}>{order.delivery_status}</span>
        </div>
      </header>

      <div className="order-columns">
        <div>
          <h3>Товары</h3>
          <ul className="summary-list">
            {order.items_info?.map((item) => (
              <li key={item.id}>
                <img src={item.product.image_url} alt="" loading="lazy" />
                <div className="s-title">{item.product.name}</div>
                <div className="s-qty">× {item.qty}</div>
                <div className="s-price">{item.price_at_purchase * item.qty} ₸</div>
              </li>
            ))}
          </ul>
          <div className="summary-total">
            Итого: <b>{order.total} ₸</b>
          </div>
        </div>

        <div>
          <h3>Доставка</h3>
          <form onSubmit={requestDelivery} className="delivery-form">
            <label>
              Адрес
              <input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
            </label>
            <label>
              Комментарий
              <textarea value={form.comment} onChange={(e) => setForm({ ...form, comment: e.target.value })} />
            </label>
            <button className="btn">Обновить доставку</button>
          </form>
        </div>
      </div>

      <section>
        <h3>Таймлайн</h3>
        {events.length === 0 ? (
          <p className="muted">Событий пока нет.</p>
        ) : (
          <ul className="timeline">
            {events.map((ev) => (
              <li key={ev.id}>
                <div>
                  <b>{ev.kind}</b>
                  <p className="muted">{new Date(ev.created_at).toLocaleString()}</p>
                </div>
                {ev.payload && <pre>{JSON.stringify(ev.payload, null, 2)}</pre>}
              </li>
            ))}
          </ul>
        )}
      </section>
    </section>
  );
}
