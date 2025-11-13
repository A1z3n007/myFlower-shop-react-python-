import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const UiContext = createContext(null)

export function UiProvider({ children }) {
  const [animationsEnabled, setAnimationsEnabled] = useState(() => {
    const v = localStorage.getItem('ui.animations')
    return v === null ? true : v === 'true'
  })
  useEffect(() => {
    const b = document.body
    if (!animationsEnabled) b.classList.add('no-anim')
    else b.classList.remove('no-anim')
    localStorage.setItem('ui.animations', String(animationsEnabled))
  }, [animationsEnabled])
  const toggleAnimations = () => setAnimationsEnabled(v => !v)

  // toasts
  const [toasts, setToasts] = useState([])
  const pushToast = (text) => {
    const id = crypto.randomUUID()
    setToasts(t => [...t, { id, text }])
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 2200)
  }
  const removeToast = (id) => setToasts(t => t.filter(x => x.id !== id))

  // modal "added"
  const [modalItem, setModalItem] = useState(null)
  const openAddModal = (item) => setModalItem(item)
  const closeAddModal = () => setModalItem(null)

  // auth modal
  const [authModal, setAuthModal] = useState({ open: false, view: "login" })
  const openAuthModal = (view = "login") => setAuthModal({ open: true, view })
  const closeAuthModal = () => setAuthModal({ open: false, view: "login" })

  const value = useMemo(() => ({
    animationsEnabled, toggleAnimations,
    toasts, pushToast, removeToast,
    modalItem, openAddModal, closeAddModal,
    authModal, openAuthModal, closeAuthModal
  }), [animationsEnabled, toasts, modalItem, authModal])

  return <UiContext.Provider value={value}>{children}</UiContext.Provider>
}

export const useUi = () => useContext(UiContext)
