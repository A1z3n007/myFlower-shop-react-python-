import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCart } from "../state/CartContext.jsx";
import { Api } from "../data/api.js";

const initialForm = {
  name: "",
  email: "",
  address: "",
  slot: "",
  comment: "",
  coupon: "",
  gift: false,
  giftMessage: "",
  card: "",
  exp: "",
  cvc: "",
};

export default function CheckoutPage() {
  const { items, total, clearCart } = useCart();
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [slots, setSlots] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [savedAddresses, setSavedAddresses] = useState([]);
  const [selectedAddress, setSelectedAddress] = useState("");
  const [discount, setDiscount] = useState(0);
  const [couponInfo, setCouponInfo] = useState(null);
  const [err, setErr] = useState("");
  const [paid, setPaid] = useState(false);
  const [checkingCoupon, setCheckingCoupon] = useState(false);

  useEffect(() => {
    Api.getDeliverySlots().then((res) => setSlots(res.slots || [])).catch(() => {});
    if (localStorage.getItem("jwt")) {
      Api.getSavedAddresses().then((res) => setSavedAddresses(res.items || [])).catch(() => {});
    }
  }, []);

  useEffect(() => {
    if (form.address.length < 4) {
      setSuggestions([]);
      return;
    }
    const id = setTimeout(() => {
      Api.autocompleteAddress(form.address)
        .then((res) => setSuggestions(res.suggestions || []))
        .catch(() => {});
    }, 300);
    return () => clearTimeout(id);
  }, [form.address]);

  const subtotal = useMemo(
    () => items.reduce((sum, { item, qty }) => sum + item.price * qty, 0),
    [items]
  );

  const grandTotal = Math.max(subtotal - discount, 0);

  const updateField = (name, value) => {
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const applyCoupon = async () => {
    if (!form.coupon.trim()) return;
    setCheckingCoupon(true);
    try {
      const res = await Api.validateCoupon(form.coupon.trim(), subtotal);
      setDiscount(res.discount || 0);
      setCouponInfo(res.snapshot);
    } catch (error) {
      setDiscount(0);
      setCouponInfo(null);
      setErr(error.message);
    } finally {
      setCheckingCoupon(false);
    }
  };

  const fillAddress = (value) => {
    updateField("address", value);
    setSuggestions([]);
  };

  const useSavedAddress = (id) => {
    setSelectedAddress(id);
    const addr = savedAddresses.find((a) => a.id === Number(id));
    if (addr) updateField("address", addr.address);
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!items.length) {
      setErr("Корзина пуста");
      return;
    }
    try {
      if (!/^\d{16}$/.test(form.card.replace(/\s+/g, ""))) {
        setErr("Введите 16 цифр карты (учебный режим)");
        return;
      }
      if (!/^\d{2}\/\d{2}$/.test(form.exp)) {
        setErr("Срок карты в формате MM/YY");
        return;
      }
      if (!/^\d{3}$/.test(form.cvc)) {
        setErr("CVC из 3 цифр");
        return;
      }

      const payload = {
        customer_name: form.name,
        email: form.email,
        address: form.address,
        delivery_address: form.address,
        delivery_slot: form.slot,
        delivery_comment: form.comment,
        coupon_code: form.coupon || undefined,
        is_gift: form.gift,
        gift_message: form.giftMessage,
        saved_address_id: selectedAddress || undefined,
        use_saved_address: form.gift ? false : !!selectedAddress,
        total: grandTotal,
        items: items.map(({ item, qty }) => ({ product_id: item.id, qty })),
      };
      const res = await Api.createOrder(payload);
      localStorage.setItem("user.email", form.email);
      clearCart();
      setPaid(true);
      setTimeout(() => navigate(`/success?order=${res.id}`, { replace: true }), 1200);
    } catch (error) {
      setErr(error.message);
    }
  };

  if (items.length === 0) return <p className="muted">В корзине пусто.</p>;

  return (
    <div className="checkout">
      <h1 className="page-title">Оформление заказа</h1>
      <div className="checkout-grid">
        <form className="checkout-form" onSubmit={submit}>
          <div className="field">
            <label>Имя</label>
            <input name="name" value={form.name} onChange={(e) => updateField("name", e.target.value)} required />
          </div>
          <div className="field">
            <label>Email</label>
            <input type="email" name="email" value={form.email} onChange={(e) => updateField("email", e.target.value)} required />
          </div>
          <div className="field">
            <label>Адрес доставки</label>
            <input name="address" value={form.address} onChange={(e) => updateField("address", e.target.value)} required />
            {suggestions.length > 0 && (
              <ul className="suggestions">
                {suggestions.map((s, idx) => (
                  <li key={idx} onClick={() => fillAddress(s.value)}>{s.value}</li>
                ))}
              </ul>
            )}
          </div>
        {savedAddresses.length > 0 && (
          <div className="field">
            <label>Мои адреса</label>
            <select
              className="field-control"
              value={selectedAddress}
              onChange={(e) => useSavedAddress(e.target.value)}
            >
              <option value="">Не выбрано</option>
              {savedAddresses.map((addr) => (
                <option key={addr.id} value={addr.id}>{addr.label || addr.address}</option>
                ))}
              </select>
            </div>
          )}
          <div className="field">
            <label>Слот доставки</label>
            <select
              className="field-control"
              value={form.slot}
              onChange={(e) => updateField("slot", e.target.value)}
            >
              <option value="">Выберите окно</option>
              {slots.map((slot) => (
                <option key={slot.value} value={slot.value}>
                  {slot.label_day}: {slot.window}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Комментарий курьеру</label>
            <textarea name="comment" value={form.comment} onChange={(e) => updateField("comment", e.target.value)} />
          </div>
          <div className="field inline">
            <input
              type="checkbox"
              id="gift"
              checked={form.gift}
              onChange={(e) => updateField("gift", e.target.checked)}
            />
            <label htmlFor="gift">Оформить как подарок</label>
          </div>
          {form.gift && (
            <div className="field">
              <label>Пожелание на открытке</label>
              <textarea
                name="giftMessage"
                value={form.giftMessage}
                onChange={(e) => updateField("giftMessage", e.target.value)}
              />
            </div>
          )}

          <div className="coupon-row">
            <input
              name="coupon"
              placeholder="Промокод"
              value={form.coupon}
              onChange={(e) => updateField("coupon", e.target.value)}
            />
            <button type="button" className="btn btn-ghost" onClick={applyCoupon} disabled={checkingCoupon}>
              {checkingCoupon ? "Проверяем..." : "Применить"}
            </button>
          </div>
          {discount > 0 && (
            <div className="toast toast-inline">
              Купон активен: −{discount} ₸ ({couponInfo?.type === "percent" ? `${couponInfo.value}%` : "фикс."})
            </div>
          )}

          <div className="field">
            <label>Карта (учебная)</label>
            <input
              name="card"
              placeholder="0000 0000 0000 0000"
              value={form.card}
              onChange={(e) => updateField("card", e.target.value)}
              required
            />
          </div>
          <div className="cols">
            <div className="field">
              <label>MM/YY</label>
              <input
                name="exp"
                placeholder="12/28"
                value={form.exp}
                onChange={(e) => updateField("exp", e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label>CVC</label>
              <input
                name="cvc"
                placeholder="123"
                value={form.cvc}
                onChange={(e) => updateField("cvc", e.target.value)}
                required
              />
            </div>
          </div>
          {err && <div className="err">{err}</div>}
          {paid && <div className="toast-inline">Оплата прошла успешно! 🎉</div>}
          <button className="btn big" type="submit">
            Оплатить {grandTotal} ₸
          </button>
        </form>

        <aside className="checkout-summary">
          <h3>Ваш заказ</h3>
          <ul className="summary-list">
            {items.map(({ item, qty }) => (
              <li key={item.id}>
                <img src={item.image_url || item.image} alt="" loading="lazy" />
                <div className="s-title">{item.name}</div>
                <div className="s-qty">× {qty}</div>
                <div className="s-price">{item.price * qty} ₸</div>
              </li>
            ))}
          </ul>
          <div className="summary-total">
            Сумма: <b>{subtotal} ₸</b>
          </div>
          {discount > 0 && (
            <div className="summary-total">
              Скидка: <b>−{discount} ₸</b>
            </div>
          )}
          <div className="summary-total grand">
            Итого: <b>{grandTotal} ₸</b>
          </div>
        </aside>
      </div>
    </div>
  );
}
