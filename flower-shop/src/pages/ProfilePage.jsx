import { useEffect, useState } from "react";
import { Api } from "../data/api.js";

export default function ProfilePage(){
  const [mine] = useState(!!localStorage.getItem("jwt"));
  const [email, setEmail] = useState(localStorage.getItem("user_email") || "");
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  const load = async ()=>{
    try{
      setErr("");
      const res = await Api.getProfile(mine ? {mine:true} : {mine:false, email});
      setData(res);
    }catch(e){ setErr("Ошибка загрузки профиля: " + e.message); }
  };

  useEffect(()=>{ load(); });

  return (
    <div className="container">
      <h1 className="page-title">Профиль</h1>

      {!mine && (
        <div className="filters">
          <input className="input" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} />
          <button className="btn" onClick={load}>Загрузить</button>
        </div>
      )}

      {err && <div className="err">{err}</div>}

      {!data ? (
        <div className="muted">Загрузка…</div>
      ) : (
        <div className="checkout-grid">
          <div className="checkout-form">
            <div className="field"><label>Имя</label><input value={data.name || ""} readOnly /></div>
            <div className="field"><label>Email</label><input value={data.email || ""} readOnly /></div>
            <div className="cols">
              <div className="field"><label>Заказов</label><input value={data.orders_count} readOnly /></div>
              <div className="field"><label>Потрачено</label><input value={`${data.total_spent} ₸`} readOnly /></div>
            </div>
            <div className="field">
              <label>Последний заказ</label>
              <input value={data.last_order_at ? new Date(data.last_order_at).toLocaleString() : "—"} readOnly />
            </div>
          </div>

          <div className="checkout-summary">
            <h3 style={{marginTop:0}}>Любимые категории</h3>
            {!data.top_categories?.length ? (
              <div className="muted">Пока нет данных</div>
            ) : (
              <ul className="summary-list">
                {data.top_categories.map((c,i)=>(
                  <li key={i}>
                    <div className="s-title">{c.category || "other"}</div>
                    <div className="s-qty">× {c.qty}</div>
                    <div className="s-price"></div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
