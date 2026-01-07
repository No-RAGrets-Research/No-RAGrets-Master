import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { MainLayout } from './components/layout/MainLayout'
import { Dashboard } from './pages/Dashboard'
import { PaperView } from './pages/PaperView'
import { GraphView } from './pages/GraphView'
import { SearchView } from './pages/SearchView'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="papers/:id" element={<PaperView />} />
          <Route path="graph" element={<GraphView />} />
          <Route path="search" element={<SearchView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
