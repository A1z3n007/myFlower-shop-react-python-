import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './index.css'
import { CartProvider } from './state/CartContext.jsx'
import { UiProvider } from './state/UIContext.jsx'
import { FavoritesProvider } from './state/FavoritesContext.jsx'
import { CompareProvider } from './state/CompareContext.jsx'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <UiProvider>
        <FavoritesProvider>
          <CompareProvider>
            <CartProvider>
              <App />
            </CartProvider>
          </CompareProvider>
        </FavoritesProvider>
      </UiProvider>
    </BrowserRouter>
  </React.StrictMode>
)

if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((err) => {
      console.error('SW registration failed', err)
    })
  })
}
