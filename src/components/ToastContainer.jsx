import { useUi } from '../state/UIContext.jsx'

export default function ToastContainer() {
  const { toasts, removeToast } = useUi()
  return (
    <div className="toast-wrap" aria-live="polite" aria-atomic="true">
      {toasts.map(t => (
        <div key={t.id} className="toast" onClick={() => removeToast(t.id)}>
          <div className="toast-dot" />
          <div className="toast-text">{t.text}</div>
        </div>
      ))}
    </div>
  )
}
