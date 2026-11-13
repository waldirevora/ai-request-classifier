import React from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";
import Portals from "./Portals.jsx";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <Portals />
  </React.StrictMode>,
);
