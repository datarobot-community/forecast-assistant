const express = require("express");
const path = require("path");
const { createProxyMiddleware } = require("http-proxy-middleware");

const app = express();
const PORT = process.env.PORT || 8080;
const FASTAPI_PORT = process.env.FASTAPI_PORT || 8001;

// Define the custom application root from environment variables
const applicationRoot = process.env.SCRIPT_NAME || "/";

// Create a router to handle all routes under applicationRoot
const router = express.Router();

// Mount the router at applicationRoot
app.use(applicationRoot, router);

app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});

// Serve static files from the React app's build directory
router.use("/", express.static(path.join(__dirname, "build")));

// Proxy FastAPI requests
router.use(
  `/fastapi`,
  createProxyMiddleware({
    target: `http://0.0.0.0:${FASTAPI_PORT}`,
    changeOrigin: true,
  })
);

// Define a catch-all route to handle client-side routing for React
router.get("/*", (req, res) => {
  res.sendFile(path.join(__dirname, "build", "index.html"));
});
