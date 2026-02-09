import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// ✅ PROFILING HABILITADO: React Profiler funciona automáticamente en desarrollo con Vite
// El Profiler de React DevTools estará disponible en modo desarrollo
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)