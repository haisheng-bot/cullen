import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter, Route, Routes } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import Dashboard from './pages/Dashboard.tsx'
import StockDetail from './pages/StockDetail.tsx'
import MarketScanner from './pages/MarketScanner.tsx'
import PortfolioResearch from './pages/PortfolioResearch.tsx'
import StrategyLibrary from './pages/StrategyLibrary.tsx'
import Reports from './pages/Reports.tsx'
import Settings from './pages/Settings.tsx'

// HashRouter (not BrowserRouter): apps/api/main.py has no SPA catch-all route today, and adding
// one is out of Phase 1 scope. Hash routes (/#/stock/AAPL) work against the single index.html
// FastAPI already serves with zero backend routing changes. Revisit if clean URLs are wanted later.
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <HashRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<Dashboard />} />
          <Route path="scanner" element={<MarketScanner />} />
          <Route path="stock/:symbol" element={<StockDetail />} />
          <Route path="portfolio" element={<PortfolioResearch />} />
          <Route path="strategy" element={<StrategyLibrary />} />
          <Route path="reports" element={<Reports />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </HashRouter>
  </StrictMode>,
)
