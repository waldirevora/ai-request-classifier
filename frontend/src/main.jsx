import React from "react";
import { createRoot } from "react-dom/client";
import Portals from "./Portals.jsx";
import "./styles.css";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <Portals />
  </React.StrictMode>,
);
