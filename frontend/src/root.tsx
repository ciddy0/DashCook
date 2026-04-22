import "./index.css";
import { Outlet, Scripts, Meta, Links, ScrollRestoration } from 'react-router';

export default function Root() {
  return (
    <html lang="en">
      <head>
        <title>Dash Cook</title>
        <Meta />
        <Links />
      </head>
      <body>
        <Outlet />
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  )
}