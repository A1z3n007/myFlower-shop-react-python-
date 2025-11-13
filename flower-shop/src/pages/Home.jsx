import { useEffect, useMemo, useState } from "react";
import Fuse from "fuse.js";
import ProductCard from "../components/ProductCard.jsx";
import FilterBar from "../components/FilterBar.jsx";
import { Api } from "../data/api.js";

export default function Home() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [sort, setSort] = useState("new");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const data = await Api.getProducts();
        setProducts(data);
        setError("");
      } catch (err) {
        console.error(err);
        setError("API не отвечает. Проверьте Django backend (http://127.0.0.1:8000).");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const categories = useMemo(() => {
    const list = Array.from(new Set(products.map((p) => p.category).filter(Boolean)));
    return ["all", ...list];
  }, [products]);

  const fuse = useMemo(
    () =>
      new Fuse(products, {
        keys: ["name", "category", "desc"],
        includeMatches: true,
        threshold: 0.35,
      }),
    [products]
  );

  const { filtered, highlights } = useMemo(() => {
    let list = products;
    let highlightMap = {};
    if (search.trim()) {
      const results = fuse.search(search.trim());
      list = results.map((res) => res.item);
      highlightMap = results.reduce((acc, entry) => {
        acc[entry.item.id] = entry.matches;
        return acc;
      }, {});
    }
    list = list.filter((p) => {
      const byCat = category === "all" || p.category === category;
      const byMin = !minPrice || p.price >= Number(minPrice);
      const byMax = !maxPrice || p.price <= Number(maxPrice);
      return byCat && byMin && byMax;
    });
    if (sort === "rating") {
      list = [...list].sort((a, b) => (b.rating_avg || 0) - (a.rating_avg || 0));
    } else {
      list = [...list].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    }
    return { filtered: list, highlights: highlightMap };
  }, [products, search, category, minPrice, maxPrice, sort, fuse]);

  return (
    <section>
      <div className="page-head">
        <h1 className="page-title">Наши букеты</h1>
        <div className="sorter">
          <label>Сортировать</label>
          <select className="select" value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="new">по новизне</option>
            <option value="rating">по рейтингу</option>
          </select>
        </div>
      </div>
      <FilterBar
        search={search}
        setSearch={setSearch}
        category={category}
        setCategory={setCategory}
        categories={categories}
        minPrice={minPrice}
        setMinPrice={setMinPrice}
        maxPrice={maxPrice}
        setMaxPrice={setMaxPrice}
      />

      {loading && <div className="muted">Загружаем каталог...</div>}
      {error && <div className="err">{error}</div>}

      {!loading && !error && (
        <>
          {filtered.length === 0 ? (
            <div className="empty">Ничего не нашли. Попробуйте изменить фильтры.</div>
          ) : (
            <div className="grid">
              {filtered.map((item, i) => (
                <ProductCard
                  key={item.id}
                  item={item}
                  idx={i}
                  highlightMatches={highlights[item.id]}
                />
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
