import { useState } from "react";
import { Api } from "../data/api.js";
import { useNavigate } from "react-router-dom";

export default function LoginPage(){
  const [email,setEmail]=useState("");
  const [password,setPassword]=useState("");
  const [err,setErr]=useState("");
  const nav = useNavigate();

  const submit = async (e) => {
    e.preventDefault(); setErr("");
    try { await Api.login({ email, password }); nav("/orders"); }
    catch(e){ setErr("Неверные данные: " + e.message); }
  };

  return (
    <div className="container">
      <h1 className="page-title">Вход</h1>
      <form className="checkout-form" onSubmit={submit} style={{maxWidth:420}}>
        {err && <div className="err">{err}</div>}
        <div className="field">
          <label>Email</label>
          <input value={email} onChange={e=>setEmail(e.target.value)} />
        </div>
        <div className="field">
          <label>Пароль</label>
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} />
        </div>
        <button className="btn">Войти</button>
      </form>
    </div>
  );
}
