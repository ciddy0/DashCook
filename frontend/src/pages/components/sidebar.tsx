import { NavLink } from 'react-router';
import { useState, useEffect } from 'react';

function Sidebar() {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved) return saved === 'dark' ? true : false;
    console.log(saved);
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark');
      document.body.setAttribute('data-theme', 'dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.body.classList.remove('dark');
      document.body.setAttribute('data-theme', 'light');
      localStorage.setItem('theme', 'light');
    }
  }, [darkMode]);
  return (
    <>
        <div className="flex flex-col items-start px-8 justify-center bg-yellow-200 dark:bg-[#222222] transition-all ease-in-out">
            <nav className="flex flex-col items-start text-[#444444] dark:text-white gap-1">
            <NavLink to="/" className="text-2xl font-[600] text-[#222222] dark:text-yellow-200">what's cookin?</NavLink>
                <button onClick={() => setDarkMode(!darkMode)} className="cursor-pointer">toggle theme</button>
                <button><NavLink to="/savedRecipes">saved recipes</NavLink></button>
                <div className="flex flex-col items-start my-2 gap-1">
                    <input className="bg-[#777777] placeholder-[#c4c4c4] text-[#222222] rounded-sm p-0.5 text-sm" placeholder="load new recipe..."></input>
                    <button><NavLink to="/recipe" className="font-semibold">
                        let's cook!
                    </NavLink></button>
                </div>
            </nav>
        </div>
    </>
  )
}

export default Sidebar;