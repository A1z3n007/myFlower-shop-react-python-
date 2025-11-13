import { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useCart } from "../state/CartContext.jsx";
import { Api } from "../data/api.js";

const RECENT_KEY = "recent.products";

function QuickBuy({ productId }) {
  const [form, setForm] = useState({ name: "", phone: "", email: "" });
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setPending(true);
    try {
      await Api.quickOrder({ ...form, product_id: productId });
      setDone(true);
      setForm({ name: "", phone: "", email: "" });
    } catch (err) {
      console.error(err);
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="quick-buy">
      <h4>Купить в 1 клик</h4>
      {done && <div className="toast toast-inline">Мы уже звоним!</div>}
      <form onSubmit={submit}>
        <input
          name="name"
          placeholder="Имя"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
        <input
          name="phone"
          placeholder="+7 700 123 45 67"
          value={form.phone}
          onChange={(e) => setForm({ ...form, phone: e.target.value })}
          required
        />
        <input
          name="email"
          type="email"
          placeholder="Email (необязательно)"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
        />
        <button className="btn" disabled={pending}>
          {pending ? "Отправляем..." : "Жду звонка"}
        </button>
      </form>
    </div>
  );
}

export default function ProductPage() {
  const { id } = useParams();
  const { addToCart } = useCart();
  const [product, setProduct] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [bundles, setBundles] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const [prod, sim, bun, rev] = await Promise.all([
          Api.getProduct(id),
          Api.getSimilarProducts(id),
          Api.getBundleSuggestions(id),
          Api.getProductReviews(id),
        ]);
        setProduct(prod);
        setSimilar(sim.items || []);
        setBundles(bun.items || []);
        setReviews(rev.results || []);
        setError("");
        const entry = {
          id: prod.id,
          name: prod.name,
          image_url: prod.image_url,
          price: prod.price,
        };
        const list = JSON.parse(localStorage.getItem(RECENT_KEY) || "[]").filter(
          (p) => p.id !== prod.id
        );
        const next = [entry, ...list].slice(0, 6);
        localStorage.setItem(RECENT_KEY, JSON.stringify(next));
        setRecent(next.slice(1));
        Api.fireAnalytics("product:view", { product_id: prod.id }).catch(() => {});
      } catch (err) {
        console.error(err);
        setError("Не удалось загрузить букет. Проверьте backend.");
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const rating = useMemo(
    () => Number(product?.rating_avg || 0).toFixed(1),
    [product]
  );

  if (loading) return <div className="muted">Загружаем...</div>;
  if (error) return <div className="err">{error}</div>;
  if (!product) return <div className="muted">Букет не найден.</div>;

  return (
    <div className="product-page">
      <div className="product-hero">
        <div className="product-media">
          <img src={product.image_url} alt={product.name} loading="lazy" />
        </div>
        <div className="product-info">
          <h1>{product.name}</h1>
          <p className="muted">Категория: {product.category || "букеты"}</p>
          <div className="product-rating">
            {Array.from({ length: 5 }).map((_, i) => (
              <span key={i} className={i < Math.round(product.rating_avg || 0) ? "star filled" : "star"}>
                ★
              </span>
            ))}
            <span>{rating} · {product.rating_count || 0} отзывов</span>
          </div>
          <div className="product-price">{product.price} ₸</div>
          <div className="product-actions">
            <button className="btn" onClick={() => addToCart(product)}>В корзину</button>
            <Link className="btn btn-ghost" to="/">Назад к каталогу</Link>
          </div>
          <p className="product-desc">{product.desc}</p>
          <QuickBuy productId={product.id} />
        </div>
      </div>

      {bundles.length > 0 && (
        <section>
          <h3>Часто покупают вместе</h3>
          <div className="grid">
            {bundles.map((b) => (
              <Link key={b.id} to={`/product/${b.id}`} className="mini-card">
                <img src={b.image_url} alt={b.name} loading="lazy" />
                <div>
                  <p>{b.name}</p>
                  <span className="price">{b.price} ₸</span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {similar.length > 0 && (
        <section>
          <h3>Похожие букеты</h3>
          <div className="grid">
            {similar.map((s) => (
              <Link key={s.id} to={`/product/${s.id}`} className="mini-card">
                <img src={s.image_url} alt={s.name} loading="lazy" />
                <div>
                  <p>{s.name}</p>
                  <span className="price">{s.price} ₸</span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {recent.length > 0 && (
        <section>
          <h3>Недавно смотрели</h3>
          <div className="grid">
            {recent.map((r) => (
              <Link key={r.id} to={`/product/${r.id}`} className="mini-card">
                <img src={r.image_url} alt={r.name} loading="lazy" />
                <div>
                  <p>{r.name}</p>
                  <span className="price">{r.price} ₸</span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section>
        <h3>Отзывы</h3>
        {reviews.length === 0 ? (
          <p className="muted">Пока нет отзывов — напишите первый!</p>
        ) : (
          <ul className="reviews">
            {reviews.map((rev) => (
              <li key={rev.id}>
                <div className="review-head">
                  <b>{rev.title || "Покупатель"}</b>
                  <span>{"★".repeat(rev.rating)}</span>
                </div>
                <p>{rev.comment}</p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
