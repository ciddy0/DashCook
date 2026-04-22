import '../App.css'
import { NavLink } from "react-router";

function Home() {

  return (
    <>
      <section id="center">
      <h1>home</h1>
      <nav className="flex flex-col">
        <NavLink to="/loading">see loading screen</NavLink>
        <NavLink to="/recipe">recipe</NavLink>
        <NavLink to="/savedRecipes">saved recipes</NavLink>
      </nav>
      </section>
    </>
  )
}

export default Home;
