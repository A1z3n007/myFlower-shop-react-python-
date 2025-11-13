import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Api } from '../data/api.js'
import { useUi } from '../state/UIContext.jsx'

export default function AddProductPage() {
  const nav = useNavigate()
  const { pushToast } = useUi()
  const [form, setForm] = useState({
    name: '', category: '', price: '', image_url: '', desc: ''
  })
  const [err, setErr] = useState('')

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const onSubmit = async (e) => {
    e.preventDefault()
    setErr('')
    try {
      const payload = { ...form, price: Number(form.price) || 0 }
      const p = await Api.createProduct(payload)
      pushToast(`Товар создан: ${p.name}`)
      nav('/')
    } catch {
      setErr('Ошибка создания. Проверь, что backend запущен.')
    }
  }

  return (
    <div className="checkout">
      <h1 className="page-title">Добавить товар</h1>
      <form className="checkout-form" onSubmit={onSubmit}>
        <div className="field"><label>Название</label><input name="name" value={form.name} onChange={onChange} required/></div>
        <div className="field"><label>Категория</label><input name="category" value={form.category} onChange={onChange} required/></div>
        <div className="field"><label>Цена (₸)</label><input name="price" value={form.price} onChange={onChange} inputMode="numeric" required/></div>
        <div className="field"><label>URL изображения</label><input name="image_url" value={form.image_url} onChange={onChange} required placeholder="https://..."/></div>
        <div className="field"><label>Описание</label><input name="desc" value={form.desc} onChange={onChange}/></div>
        {err && <div className="err">{err}</div>}
        <button className="btn big" type="submit">Сохранить</button>
      </form>
    </div>
  )
}
