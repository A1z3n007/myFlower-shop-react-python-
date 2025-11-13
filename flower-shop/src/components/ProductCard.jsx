import { Link } from "react-router-dom";
import { useMemo, useRef } from "react";
import { useCart } from "../state/CartContext.jsx";
import { useFavorites } from "../state/FavoritesContext.jsx";
import { useCompare } from "../state/CompareContext.jsx";
import { useUi } from "../state/UIContext.jsx";

export default function ProductCard({ item, idx = 0, highlightMatches = [] }) {
  const { addToCart } = useCart();
  const { toggleFavorite, isFavorite } = useFavorites();
  const { addToCompare, isInCompare } = useCompare();
  const { pushToast } = useUi();
  const ref = useRef(null);

  const onMove = (e) => {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const x = e.clientX - r.left;
    const y = e.clientY - r.top;
    const rx = (y / r.height - 0.5) * -8;
    const ry = (x / r.width - 0.5) * 10;
    el.style.transform = `perspective(800px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(-2px)`;
  };
  const onLeave = () => {
    const el = ref.current;
    if (el) el.style.transform = "";
  };

  const img = item.image_url || item.image;
  const fav = isFavorite(item.id);
  const compared = isInCompare(item.id);
  const rating = Number(item.rating_avg || 0).toFixed(1);

  const highlightedName = useMemo(() => {
    const nameMatch = (highlightMatches || []).find((m) => m.key === "name");
    if (!nameMatch) return item.name;
    const ranges = nameMatch.indices;
    const parts = [];
    let last = 0;
    ranges.forEach(([start, end], i) => {
      if (start > last) parts.push(item.name.slice(last, start));
      parts.push(<mark key={`h-${i}`}>{item.name.slice(start, end + 1)}</mark>);
      last = end + 1;
    });
    if (last < item.name.length) parts.push(item.name.slice(last));
    return parts;
  }, [highlightMatches, item.name]);

  return (
    <article
      ref={ref}
      className="card"
      style={{ "--i": idx }}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
    >
      <Link to={`/product/${item.id}`} className="card-media">
        <img src={img} alt={item.name} loading="lazy" />
        <button
          type="button"
          className={`heart ${fav ? "active" : ""}`}
          onClick={(e) => {
            e.preventDefault();
            toggleFavorite(item.id);
          }}
          aria-label="Избранное"
        />
      </Link>
      <div className="card-body">
        <Link to={`/product/${item.id}`} className="card-title link-plain">
          {highlightedName}
        </Link>
        <p className="card-cat">{item.category || "букет"}</p>
        <div className="card-rating" aria-label={`Рейтинг ${rating}`}>
          {Array.from({ length: 5 }).map((_, i) => (
            <span
              key={i}
              className={i < Math.round(item.rating_avg || 0) ? "star filled" : "star"}
            >
              ★
            </span>
          ))}
          <span className="rating-number">{rating}</span>
        </div>
        <div className="card-footer">
          <span className="price">{item.price} ₸</span>
          <div className="actions">
            <button
              className={`btn btn-ghost ${compared ? "active" : ""}`}
              onClick={() => {
                addToCompare(item);
                pushToast("Добавлено в сравнение");
              }}
            >
              {compared ? "В сравнении" : "Сравнить"}
            </button>
            <button className="btn btn-shine" onClick={() => addToCart(item)}>
              В корзину
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}
