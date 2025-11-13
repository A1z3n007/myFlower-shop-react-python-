import { createContext, useContext, useEffect, useMemo, useState } from "react";

const CompareContext = createContext(null);
const STORAGE_KEY = "compare.ids";

export function CompareProvider({ children }) {
  const [ids, setIds] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
  }, [ids]);

  const add = (product) => {
    setIds((prev) => {
      if (prev.find((p) => p.id === product.id)) return prev;
      return [...prev.slice(-2), product]; // max 3
    });
  };

  const remove = (id) => {
    setIds((prev) => prev.filter((p) => p.id !== id));
  };

  const value = useMemo(
    () => ({
      compareItems: ids,
      addToCompare: add,
      removeFromCompare: remove,
      clearCompare: () => setIds([]),
      isInCompare: (id) => ids.some((p) => p.id === id),
    }),
    [ids]
  );

  return <CompareContext.Provider value={value}>{children}</CompareContext.Provider>;
}

export const useCompare = () => useContext(CompareContext);
