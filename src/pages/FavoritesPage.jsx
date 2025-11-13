import { useEffect, useState } from "react";
import { Api } from "../data/api.js";
import ProductCard from "../components/ProductCard.jsx";
import { useFavorites } from "../state/FavoritesContext.jsx";

export default function FavoritesPage() {
  const { favorites, reloadFavorites } = useFavorites();
  const [recommended, setRecommended] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const mine = !!localStorage.getItem("jwt");
        const res = await Api.getFavorites(mine ? { mine: true } : {});
        setRecommended(res.recommended || []);
        setErr("");
      } catch (error) {
        setErr(error.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <section>
      <div className="page-head">
        <h1 className="page-title">Избранное</h1>
        <button className="btn btn-ghost" onClick={reloadFavorites}>Обновить</button>
      </div>
      {err && <div className="err">{err}</div>}
      {favorites.length === 0 ? (
        <div className="empty">Добавьте сердечком понравившиеся букеты.</div>
      ) : (
        <div className="grid">
          {favorites.map((fav, idx) => (
            <ProductCard key={fav.product?.id || fav.id} item={fav.product || fav} idx={idx} />
          ))}
        </div>
      )}

      <h3 style={{ marginTop: 40 }}>Рекомендации для вас</h3>
      {loading ? (
        <p className="muted">Секундочку...</p>
      ) : (
        <div className="grid">
          {recommended.map((item, idx) => (
            <ProductCard key={`rec-${item.id}`} item={item} idx={idx} />
          ))}
        </div>
      )}
    </section>
  );
}
