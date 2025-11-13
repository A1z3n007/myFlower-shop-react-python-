import { useEffect, useState } from "react";
import { Api } from "../api.js";
import { Link } from "react-router-dom";

const OST = { created:'создан', processing:'в обработке', delivering:'доставка', completed:'завершён', canceled:'отменён' };
const DST = { none:'нет', pending:'в ожидании', scheduled:'назначена', out_for_delivery:'в пути', delivered:'доставлено', failed:'неудача' };

export default function MyOrdersPage(){
  const [orders,setOrders]=useState([]);
  const [email,setEmail]=useState(localStorage.getItem("user_email")||"");
  const [mine]=useState(!!localStorage.getItem("jwt"));
  const [q,setQ]=useState({ status:"", dstatus:"" });

  const load = async ()=>{
    const data = await Api.getOrders(mine ? {mine:true} : {email});
    setOrders(data);
  };
  useEffect(()=>{ load(); });

  const filtered = orders.filter(o => (!q.status || o.status===q.status) && (!q.dstatus || o.delivery_status===q.dstatus));

  return (
    <div className="container">
      <h1 className="page-title">Мои заказы</h1>
      <div className="filters">
        <label className="select"> 
          <select value={q.status} onChange={e=>setQ({...q,status:e.target.value})}>
            <option value="">Все статусы</option>
            {Object.keys(OST).map(k=><option key={k} value={k}>{OST[k]}</option>)}
          </select>
        </label>
        <label className="select">
          <select value={q.dstatus} onChange={e=>setQ({...q,dstatus:e.target.value})}>
            <option value="">Доставка</option>
            {Object.keys(DST).map(k=><option key={k} value={k}>{DST[k]}</option>)}
          </select>
        </label>
        {!mine && (
          <>
            <input className="input" placeholder="Email для поиска" value={email} onChange={e=>setEmail(e.target.value)} />
            <button className="btn" onClick={load}>Найти</button>
          </>
        )}
      </div>

      <div className="order-list">
        {filtered.map(o=>(
          <div key={o.id} className="order-card">
            <div className="order-head">
              <div><b>Заказ #{o.id}</b></div>
              <div className="muted">{new Date(o.created_at).toLocaleString()}</div>
              <div className="order-sum">Итого: <b>{o.total} ₸</b></div>
            </div>
            <div className="grid2">
              <div>Статус: <span className={`st-badge st-${o.status}`}>{OST[o.status] || o.status}</span></div>
              <div>Доставка: <span className={`dl-badge dl-${o.delivery_status}`}>{DST[o.delivery_status] || o.delivery_status}</span></div>
            </div>
            {o.rating ? <div className="muted">Оценка: {"★".repeat(o.rating)}{"☆".repeat(5-o.rating)} {o.rating_comment ? `— ${o.rating_comment}` : ""}</div> : null}
            <div style={{marginTop:8}}>
              <Link className="btn btn-ghost" to={`/orders/${o.id}`}>Подробнее</Link>
            </div>
          </div>
        ))}
        {!filtered.length && <div className="empty">Заказов нет.</div>}
      </div>
    </div>
  );
}
