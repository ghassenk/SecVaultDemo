import './App.css'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>🔐 SecureVault</h1>
        <p>Your personal secrets manager</p>
      </header>
      <main className="app-main">
        <div className="status-card">
          <h2>Backend Status</h2>
          <p>Phase 1 Complete - Frontend scaffold ready</p>
          <p className="hint">
            Full authentication UI will be added in Phase 5
          </p>
        </div>
      </main>
    </div>
  )
}

export default App
