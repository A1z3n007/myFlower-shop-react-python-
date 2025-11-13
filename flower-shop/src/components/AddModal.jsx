import { useEffect } from 'react'
import { useUi } from '../state/UIContext.jsx'

export default function AddModal() {
  const { modalItem, closeAddModal } = useUi()

  useEffect(() => {
    if (!modalItem) return
    const t = setTimeout(closeAddModal, 1700)
    return () => clearTimeout(t)
  }, [modalItem, closeAddModal])

  if (!modalItem) return null
  const img = modalItem.image_url || modalItem.image

  return (
    <div className="modal-overlay" onClick={closeAddModal}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <img src={img} alt="" />
        <div className="modal-body">
          <div className="modal-title">Добавлено в корзину</div>
          <div className="modal-sub">{modalItem.name}</div>
        </div>
      </div>
    </div>
  )
}
