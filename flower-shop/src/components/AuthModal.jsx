import { useState } from "react";
import { Api } from "../data/api.js";
import { useUi } from "../state/UIContext.jsx";

export default function AuthModal() {
  const { authModal, closeAuthModal, openAuthModal, pushToast } = useUi();
  const [form, setForm] = useState({ email: "", password: "", name: "" });
  const [err, setErr] = useState("");

  if (!authModal.open) return null;

  const isLogin = authModal.view === "login";

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    try {
      setErr("");
      if (isLogin) {
        await Api.login({ email: form.email, password: form.password });
        pushToast("Вы вошли");
      } else {
        await Api.register({
          email: form.email,
          password: form.password,
          name: form.name,
        });
        pushToast("Готово! Теперь войдите");
        openAuthModal("login");
        return;
      }
      closeAuthModal();
    } catch (error) {
      setErr(error.message);
    }
  };

  const switchView = () => {
    setErr("");
    setForm({ email: "", password: "", name: "" });
    openAuthModal(isLogin ? "register" : "login");
  };

  return (
    <div className="modal-overlay" onClick={closeAuthModal}>
      <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
        <button className="auth-close" onClick={closeAuthModal} aria-label="Закрыть">
          ×
        </button>
        <h2>{isLogin ? "Вход" : "Регистрация"}</h2>
        <form onSubmit={submit} className="auth-form">
          {!isLogin && (
            <label>
              <span>Имя</span>
              <input name="name" value={form.name} onChange={onChange} required />
            </label>
          )}
          <label>
            <span>Email</span>
            <input type="email" name="email" value={form.email} onChange={onChange} required />
          </label>
          <label>
            <span>Пароль</span>
            <input type="password" name="password" value={form.password} onChange={onChange} required />
          </label>
          {err && <div className="err">{err}</div>}
          <button className="btn big" type="submit">
            {isLogin ? "Войти" : "Создать аккаунт"}
          </button>
        </form>
        <button className="link switch-link" type="button" onClick={switchView}>
          {isLogin ? "Создать аккаунт" : "У меня уже есть аккаунт"}
        </button>
      </div>
    </div>
  );
}
