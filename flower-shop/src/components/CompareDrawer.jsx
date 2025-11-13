import { useMemo } from "react";
import { Link } from "react-router-dom";
import { useCompare } from "../state/CompareContext.jsx";

export default function CompareDrawer() {
  const { compareItems, removeFromCompare, clearCompare } = useCompare();
  const open = compareItems.length > 0;

  const specs = useMemo(() => {
    if (!compareItems.length) return [];
    const keys = ["category", "price"];
    return keys.map((key) => ({
      key,
      label: key === "category" ? "Категория" : "Цена",
      values: compareItems.map((item) =>
        key === "price" ? `${item.price} ₸` : item[key] || "—"
      ),
    }));
  }, [compareItems]);

  return (
    <aside className={`compare-drawer${open ? " open" : ""}`}>
      <div className="compare-head">
        <strong>Сравнение</strong>
        <div style={{display:"flex",gap:"10px",alignItems:"center"}}>
          {open && <Link className="link" to="/compare">Открыть страницу</Link>}
          {open && <button className="link" onClick={clearCompare}>Очистить</button>}
        </div>
      </div>
      {!open ? (
        <p className="muted tiny">Добавьте до 3 букетов для быстрого сравнения.</p>
      ) : (
        <div className="compare-body">
          <div className="compare-grid">
            {compareItems.map((item) => (
              <div key={item.id} className="compare-card">
                <button className="compare-remove" onClick={() => removeFromCompare(item.id)}>×</button>
                <img src={item.image_url || item.image} alt={item.name} loading="lazy" />
                <Link to={`/product/${item.id}`} className="link-plain">{item.name}</Link>
                <div className="price">{item.price} ₸</div>
              </div>
            ))}
          </div>
          <div className="compare-specs">
            {specs.map((spec) => (
              <div key={spec.key} className="spec-row">
                <span>{spec.label}</span>
                {spec.values.map((val, idx) => (
                  <span key={`${spec.key}-${idx}`}>{val}</span>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </aside>
  );
}
