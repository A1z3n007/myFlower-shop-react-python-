import { useState } from "react";
import { Api } from "../data/api.js";
import { useNavigate } from "react-router-dom";

export default function RegisterPage(){
  const [name,setName]=useState("");
  const [email,setEmail]=useState("");
  const [password,setPassword]=useState("");
  const [ok,setOk]=useState(false);
  const [err,setErr]=useState("");
  const nav = useNavigate();

  const submit = async (e)=>{
    e.preventDefault(); setErr("");
    try{ await Api.register({ name, email, password }); setOk(true); setTimeout(()=>nav("/login"), 1000); }
    catch(e){ setErr("Ошибка: "+e.message); }
  };

  return (
    <div className="container">
      <h1 className="page-title">Регистрация</h1>
      <form className="checkout-form" onSubmit={submit} style={{maxWidth:420}}>
        {ok && <div className="toast">Создано! Теперь войдите.</div>}
        {err && <div className="err">{err}</div>}
        <div className="field"><label>Имя</label><input value={name} onChange={e=>setName(e.target.value)} /></div>
        <div className="field"><label>Email</label><input value={email} onChange={e=>setEmail(e.target.value)} /></div>
        <div className="field"><label>Пароль</label><input type="password" value={password} onChange={e=>setPassword(e.target.value)} /></div>
        <button className="btn">Создать аккаунт</button>
      </form>
    </div>
  );
}
