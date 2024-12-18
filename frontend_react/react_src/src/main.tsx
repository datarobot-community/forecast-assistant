import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter as Router } from "react-router-dom";
import "@fontsource/dm-sans/300.css";
import "@fontsource/dm-sans/400.css";
import "@fontsource/dm-sans/500.css";
import "@fontsource/dm-sans/600.css";
import "@fontsource/dm-sans/700.css";
import App from "./App";
import "./index.css";

let basename = undefined;
if (import.meta.env.MODE === "production") {
  // eg. https://app.datarobot.com/custom_applications/{appId}/ -> /custom_applications/{appId}/
  basename = window.location.pathname.split("/").slice(0, 3).join("/");
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Router basename={basename}>
      <App />
    </Router>
  </React.StrictMode>
);
