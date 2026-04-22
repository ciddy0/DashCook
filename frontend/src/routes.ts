import {
    type RouteConfig,
} from '@react-router/dev/routes';
import { flatRoutes } from '@react-router/fs-routes';

export default flatRoutes({
    ignoredRouteFiles: ['home.tsx'],
    rootDirectory: "routes",
}) satisfies RouteConfig;

// export default [
//     {
//         path: "/",
//         file: "./App.tsx",
//         children: [
//             {
//                 path: "/loading",
//                 file: "./routes/loading.tsx",
//             },
//             {
//                 path: "/recipe",
//                 file: "./routes/recipe.tsx",
//             },
//             {
//                 path: "/savedRecipes",
//                 file: "./routes/savedRecipes.tsx",
//             },
//         ]
//     }
// ] satisfies RouteConfig;