import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { BrowserRouter, Routes, Route } from 'react-router';
import Loading from './pages/loading.tsx'
import Recipe from './pages/recipe.tsx'
import SavedRecipes from './pages/savedRecipes.tsx'
import Error from './pages/$.tsx'
import Sidebar from './pages/components/sidebar.tsx'

createRoot(document.getElementById('root') as HTMLElement).render(
    <StrictMode>
    <BrowserRouter>
      <div className="h-screen w-screen flex">
      <Sidebar />
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="*" element={<Error />} />
          <Route path="/loading" element={<Loading />} />
          <Route path="/recipe" element={<Recipe />} />
          <Route path="/savedRecipes" element={<SavedRecipes />} />
        </Routes>
      </div>
      </BrowserRouter>
    </StrictMode>,
);