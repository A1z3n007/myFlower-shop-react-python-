import { createContext, useContext, useEffect, useMemo, useState, useCallback } from "react";
import { Api } from "../data/api.js";
import { useUi } from "./UIContext.jsx";

const FavoritesContext = createContext(null);

export function FavoritesProvider({ children }) {
  const { pushToast } = useUi();
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const mine = !!localStorage.getItem("jwt");
      const email = localStorage.getItem("user.email");
      if (!mine && !email) {
        setFavorites([]);
        return;
      }
      const res = await Api.getFavorites(mine ? { mine: true } : { mine: false, email });
      setFavorites(res.favorites || res.buy_again || []);
    } catch (err) {
      console.error("favorites load failed", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const isFavorite = useCallback(
    (id) => favorites.some((fav) => fav.product?.id === id || fav.id === id),
    [favorites]
  );

  const toggleFavorite = async (productId) => {
    try {
      const res = await Api.toggleFavorite(productId, "toggle");
      pushToast(res?.favorited ? "Добавлено в избранное" : "Удалено из избранного");
      load();
    } catch (err) {
      pushToast("Не удалось обновить избранное");
      console.error(err);
    }
  };

  const value = useMemo(
    () => ({
      favorites,
      loading,
      count: favorites.length,
      isFavorite,
      toggleFavorite,
      reloadFavorites: load,
    }),
    [favorites, loading, isFavorite, load]
  );

  return <FavoritesContext.Provider value={value}>{children}</FavoritesContext.Provider>;
}

export const useFavorites = () => useContext(FavoritesContext);
