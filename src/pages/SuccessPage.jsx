import { Link, useLocation } from 'react-router-dom'

export default function SuccessPage() {
  const params = new URLSearchParams(useLocation().search)
  const orderId = params.get('order') || 'ORDER'

  return (
    <div className="success">
      <div className="success-card">
        <div className="success-icon">✓</div>
        <h1>Заказ оформлен!</h1>
        <p className="muted">Номер заказа: <b>{orderId}</b></p>
        <div style={{display:'flex', gap:10, justifyContent:'center'}}>
          <Link to="/" className="btn btn-ghost">На главную</Link>
          <Link to={`/orders/${orderId}`} className="btn">Открыть детали заказа</Link>
        </div>
      </div>
    </div>
  )
}
