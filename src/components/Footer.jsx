export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <p>© {new Date().getFullYear()} FlowerShop. Все права защищены.</p>
        <p className="muted">Учебный проект (Vite + React)</p>
      </div>
    </footer>
  )
}
