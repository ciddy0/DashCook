import type { BrowseRecipe } from "../types";

/** Real URL shown as the paster placeholder — submitting an empty input extracts this. */
export const EXAMPLE_RECIPE_URL =
  "https://coupleinthekitchen.com/nobu-black-cod-recipe/";

/**
 * Dummy stand-in for the upcoming `GET /recipes` backend route.
 * Categories will come from the clustering work — for now they're hand-picked.
 */
export const DUMMY_DB_RECIPES: BrowseRecipe[] = [
  {
    title: "Nobu Black Cod",
    source_url: "https://coupleinthekitchen.com/nobu-black-cod-recipe/",
    image_url: null,
    distance: 0,
    category: "Seafood",
  },
  {
    title: "Garlic Butter Shrimp",
    source_url: "https://www.recipetineats.com/garlic-butter-shrimp/",
    image_url: null,
    distance: 0,
    category: "Seafood",
  },
  {
    title: "Braised Short Ribs",
    source_url: "https://tastesbetterfromscratch.com/braised-short-ribs/",
    image_url: null,
    distance: 0,
    category: "Comfort Food",
  },
  {
    title: "Chicken Pot Pie",
    source_url: "https://tastesbetterfromscratch.com/chicken-pot-pie/",
    image_url: null,
    distance: 0,
    category: "Comfort Food",
  },
  {
    title: "Baked Mac and Cheese",
    source_url: "https://www.recipetineats.com/baked-mac-and-cheese/",
    image_url: null,
    distance: 0,
    category: "Comfort Food",
  },
  {
    title: "Vietnamese Pho",
    source_url: "https://www.recipetineats.com/vietnamese-pho-recipe/",
    image_url: null,
    distance: 0,
    category: "Soups",
  },
  {
    title: "Creamy Tomato Soup",
    source_url: "https://www.gimmesomeoven.com/creamy-tomato-soup/",
    image_url: null,
    distance: 0,
    category: "Soups",
  },
  {
    title: "Spaghetti Carbonara",
    source_url: "https://www.recipetineats.com/carbonara/",
    image_url: null,
    distance: 0,
    category: "Pasta",
  },
  {
    title: "Creamy Garlic Parmesan Pasta",
    source_url: "https://www.gimmesomeoven.com/garlic-parmesan-pasta/",
    image_url: null,
    distance: 0,
    category: "Pasta",
  },
  {
    title: "Fudgy Brownies",
    source_url: "https://sallysbakingaddiction.com/chewy-fudgy-homemade-brownies/",
    image_url: null,
    distance: 0,
    category: "Desserts",
  },
  {
    title: "Chocolate Chip Cookies",
    source_url: "https://sallysbakingaddiction.com/chocolate-chip-cookies/",
    image_url: null,
    distance: 0,
    category: "Desserts",
  },
  {
    title: "Classic Cheesecake",
    source_url: "https://sallysbakingaddiction.com/classic-cheesecake/",
    image_url: null,
    distance: 0,
    category: "Desserts",
  },
];
