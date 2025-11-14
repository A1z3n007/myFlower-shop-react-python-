import { NavLink, Link } from "react-router-dom";
import { useMemo } from "react";
import { useFavorites } from "../state/FavoritesContext.jsx";
import { useCompare } from "../state/CompareContext.jsx";
import { useUi } from "../state/UIContext.jsx";
import { Api } from "../data/api.js";

function NavItem({ to, icon, children }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
    >
      <img className="nav-icon" src={icon} alt="" aria-hidden="true" />
      <span>{children}</span>
    </NavLink>
  );
}

export default function Header() {
  const { count: favoritesCount } = useFavorites();
  const { compareItems } = useCompare();
  const { openAuthModal } = useUi();
  const isAuth = !!localStorage.getItem("jwt");
  const userEmail = localStorage.getItem("user_email") || "";
  const initials = useMemo(
    () => (userEmail ? userEmail[0].toUpperCase() : "U"),
    [userEmail]
  );

  const handleLogout = () => {
    Api.logout();
    window.location.reload();
  };

  return (
    <header className="header">
      <div className="container header-inner">
        <Link to="/" className="logo">
          <img className="logo-icon" src="/icons/flower.svg" alt="" />
          <b>Flower</b>
          <span>Shop</span>
        </Link>

        <nav className="nav">
          <NavItem to="/" icon="/icons/home.svg">
            Главная
          </NavItem>
          <NavItem to="/favorites" icon="/icons/heart.svg">
            FAVORITES
            {favoritesCount > 0 && <span className="badge">{favoritesCount}</span>}
          </NavItem>
          <NavItem to="/orders" icon="/icons/clipboard.svg">
            Заказы
          </NavItem>
          <NavItem to="/cart" icon="/icons/cart.svg">
            Корзина
          </NavItem>
          <NavItem to="/compare" icon="/icons/flower.svg">
            Compare
            {compareItems.length > 0 && <span className="badge">{compareItems.length}</span>}
          </NavItem>

          {isAuth ? (
            <div className="nav-auth">
              <Link to="/profile" className="avatar-pill" title={userEmail}>
                <span className="avatar-dot">{initials}</span>
                <span className="avatar-text">Профиль</span>
              </Link>
              <button
                className="nav-link ghost logout-btn"
                type="button"
                onClick={handleLogout}
              >
                <img className="nav-icon" src="/icons/user-circle.svg" alt="" />
                Выйти
              </button>
            </div>
          ) : (
            <>
              <button
                className="nav-link ghost"
                type="button"
                onClick={() => openAuthModal("login")}
              >
                <img className="nav-icon" src="/icons/user-circle.svg" alt="" />
                Войти
              </button>
              <button
                className="nav-link ghost"
                type="button"
                onClick={() => openAuthModal("register")}
              >
                <img className="nav-icon" src="/icons/user-circle.svg" alt="" />
                Регистрация
              </button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
