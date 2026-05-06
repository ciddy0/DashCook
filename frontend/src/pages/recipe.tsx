import '../App.css'

function Recipe() {
  return (
    <>
      <div className="flex flex-col justify-center px-8 items-start text-left">
        <h1>some dish</h1>
        <br/>
        <h2>ingredients</h2>
        <ul>
          <li>ingredient 1</li>
          <li>ingredient 2</li>
          <li>ingredient 3</li>
        </ul>
        <br/>
        <h2>instructions</h2>
        <ol>
          <li>step 1</li>
          <li>step 2</li>
          <li>step 3</li>
        </ol>
      </div>
    </>
  )
}

export default Recipe;
