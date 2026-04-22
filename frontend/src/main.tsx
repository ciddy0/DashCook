import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { BrowserRouter, Route, Routes } from 'react-router';
import Loading from './routes/loading.tsx';
import Recipe from './routes/recipe.tsx';
import SavedRecipes from './routes/savedRecipes.tsx';

createRoot(document.getElementById('root') as HTMLElement).render(
    <StrictMode>
    <BrowserRouter>
        <App />
      </BrowserRouter>
    </StrictMode>,
);