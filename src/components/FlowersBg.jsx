import { useEffect, useMemo } from 'react'
import { PETAL_ICON_URL } from '../assets/icons.js'

export default function FlowersBg() {
  const petals = useMemo(() => {
    const n = 24
    return Array.from({ length: n }).map((_, i) => {
      const size = Math.round(16 + Math.random() * 28)
      const left = Math.round(Math.random() * 100)
      const delay = (Math.random() * 12).toFixed(2)
      const dur = (12 + Math.random() * 18).toFixed(2)
      const drift = (Math.random() * 40 - 20).toFixed(0)
      const rot = Math.round(Math.random() * 360)
      return { i, size, left, delay, dur, drift, rot }
    })
  }, [])

  useEffect(() => {
    const root = document.documentElement
    const onMouse = (e) => {
      root.style.setProperty('--px', (e.clientX / innerWidth).toFixed(3))
      root.style.setProperty('--py', (e.clientY / innerHeight).toFixed(3))
    }
    const onScroll = () => root.style.setProperty('--scroll', String(scrollY))
    window.addEventListener('mousemove', onMouse)
    window.addEventListener('scroll', onScroll, { passive: true })
    onScroll()
    return () => { window.removeEventListener('mousemove', onMouse); window.removeEventListener('scroll', onScroll) }
  }, [])

  return (
    <>
      <div className="bg-flowers" aria-hidden>
        {petals.map(p => (
          <span key={p.i} className="petal" style={{
            '--size': `${p.size}px`,
            '--left': `${p.left}%`,
            '--delay': `${p.delay}s`,
            '--dur': `${p.dur}s`,
            '--drift': `${p.drift}px`,
            '--rot': `${p.rot}deg`,
          }}>
            <img src={PETAL_ICON_URL} alt="" />
          </span>
        ))}
      </div>
      <div className="bg-mask" aria-hidden />
    </>
  )
}
