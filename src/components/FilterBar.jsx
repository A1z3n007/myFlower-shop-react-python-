export default function FilterBar({
  search,
  setSearch,
  category,
  setCategory,
  categories,
  minPrice,
  setMinPrice,
  maxPrice,
  setMaxPrice,
}) {
  return (
    <section className="filters">
      <input
        className="input"
        type="text"
        placeholder="Поиск по названию или описанию..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <select className="select" value={category} onChange={(e) => setCategory(e.target.value)}>
        {categories.map((cat) => (
          <option key={cat} value={cat}>
            {cat === "all" ? "Все категории" : cat}
          </option>
        ))}
      </select>

      <div className="price-range">
        <input
          className="input"
          type="number"
          min="0"
          placeholder="Мин. цена"
          value={minPrice}
          onChange={(e) => setMinPrice(e.target.value)}
        />
        <span className="dash">—</span>
        <input
          className="input"
          type="number"
          min="0"
          placeholder="Макс. цена"
          value={maxPrice}
          onChange={(e) => setMaxPrice(e.target.value)}
        />
      </div>
    </section>
  );
}
