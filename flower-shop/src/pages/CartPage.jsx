import { Link } from 'react-router-dom'
import { useCart } from '../state/CartContext.jsx'

export default function CartPage() {
  const { items, total, removeFromCart, clearCart } = useCart()

  return (
    <div className="cart-page">
      <h1 className="page-title">Корзина</h1>

      {items.length === 0 ? (
        <div className="empty">
          Корзина пуста. <Link to="/" className="link">Перейти в каталог</Link>
        </div>
      ) : (
        <>
          <div className="cart-list">
            {items.map(({ item, qty }) => {
              const img = item.image_url || item.image
              return (
                <div key={item.id} className="cart-row">
                  <img src={img} alt={item.name} className="cart-thumb" />
                  <div className="cart-info">
                    <Link to={`/product/${item.id}`} className="cart-title">{item.name}</Link>
                    <div className="muted">{item.category}</div>
                  </div>
                  <div className="cart-qty">× {qty}</div>
                  <div className="cart-price">{item.price * qty} ₸</div>
                  <button className="btn btn-danger" onClick={() => removeFromCart(item.id)}>Удалить</button>
                </div>
              )
            })}
          </div>

          <div className="cart-total">
            <div className="cart-sum">Итого: <b>{total} ₸</b></div>
            <div className="cart-actions">
              <button className="btn btn-ghost" onClick={clearCart}>Очистить</button>
              <Link className="btn" to="/checkout">Перейти к оформлению</Link>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
