import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useUi } from "./UIContext.jsx";
import { Api } from "../data/api.js";

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const { pushToast, openAddModal } = useUi();
  const [items, setItems] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("cart.items") || "[]");
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem("cart.items", JSON.stringify(items));
  }, [items]);

  const addToCart = (item) => {
    setItems((prev) => {
      const idx = prev.findIndex((entry) => entry.item.id === item.id);
      if (idx >= 0) {
        const copy = [...prev];
        copy[idx] = { ...copy[idx], qty: copy[idx].qty + 1 };
        return copy;
      }
      return [...prev, { item, qty: 1 }];
    });
    openAddModal(item);
    pushToast(`В корзине: ${item.name}`);
    Api.fireAnalytics("cart:add", { product_id: item.id }).catch(() => {});
  };

  const removeFromCart = (id) => setItems((prev) => prev.filter((entry) => entry.item.id !== id));
  const clearCart = () => setItems([]);
  const count = useMemo(() => items.reduce((sum, entry) => sum + entry.qty, 0), [items]);
  const total = useMemo(
    () => items.reduce((sum, entry) => sum + entry.item.price * entry.qty, 0),
    [items]
  );

  const value = { items, addToCart, removeFromCart, clearCart, count, total, setItems };
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export const useCart = () => useContext(CartContext);
