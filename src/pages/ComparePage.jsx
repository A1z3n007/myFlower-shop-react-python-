import { Link } from "react-router-dom";
import { useCompare } from "../state/CompareContext.jsx";

export default function ComparePage() {
  const { compareItems, clearCompare, removeFromCompare } = useCompare();

  if (compareItems.length === 0) {
    return (
      <div className="empty">
        Пока ничего не выбрано. Добавьте букеты кнопкой «Сравнить» и вернитесь сюда.
      </div>
    );
  }

  return (
    <section>
      <div className="page-head">
        <h1 className="page-title">Сравнение букетов</h1>
        <button className="btn btn-ghost" onClick={clearCompare}>Очистить</button>
      </div>

      <div className="compare-grid large">
        {compareItems.map((item) => (
          <article key={item.id} className="compare-card">
            <button className="compare-remove" onClick={() => removeFromCompare(item.id)}>×</button>
            <img src={item.image_url || item.image} alt={item.name} loading="lazy" />
            <h3>{item.name}</h3>
            <p className="muted">{item.category}</p>
            <div className="price">{item.price} ₸</div>
            <Link className="btn btn-ghost" to={`/product/${item.id}`}>Подробнее</Link>
          </article>
        ))}
      </div>
    </section>
  );
}
