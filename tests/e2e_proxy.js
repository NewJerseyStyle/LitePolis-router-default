/**
 * LitePolis E2E Test Proxy Server
 * 
 * This server:
 * 1. Serves the Polis frontend static files
 * 2. Proxies /api/v3/* requests to LitePolis backend
 * 
 * Usage:
 * 1. Build Polis frontend first: cd polis && npm run build
 * 2. Start LitePolis backend: python run_server.py
 * 3. Start this proxy: node e2e_proxy.js
 * 4. Run Cypress tests: cd polis/e2e && npm test
 */

const http = require('http');
const httpProxy = require('http-proxy');
const serveStatic = require('serve-static');
const finalhandler = require('finalhandler');
const path = require('path');

const LITEPOLIS_PORT = process.env.LITEPOLIS_PORT || 8000;
const PROXY_PORT = process.env.PROXY_PORT || 3000;
const FRONTEND_BUILD_PATH = process.env.FRONTEND_BUILD_PATH || './polis/file-server/build';

// Create proxy instance
const proxy = httpProxy.createProxyServer({
  target: `http://localhost:${LITEPOLIS_PORT}`,
  changeOrigin: true,
});

// Static file server for frontend
const serve = serveStatic(FRONTEND_BUILD_PATH, {
  index: ['index.html'],
  fallthrough: true,
});

// Create server
const server = http.createServer((req, res) => {
  // Log requests
  console.log(`${new Date().toISOString()} ${req.method} ${req.url}`);

  // Proxy API requests to LitePolis backend
  if (req.url.startsWith('/api/')) {
    proxy.web(req, res, (err) => {
      if (err) {
        console.error('Proxy error:', err);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Proxy error' }));
      }
    });
    return;
  }

  // Serve static files for frontend
  serve(req, res, (err) => {
    if (err) {
      console.error('Static file error:', err);
      finalhandler(req, res)(err);
      return;
    }
    
    // For SPA routing, serve index.html for non-API routes
    if (!req.url.includes('.') && !req.url.startsWith('/api/')) {
      req.url = '/index.html';
      serve(req, res, finalhandler(req, res));
    }
  });
});

// Handle proxy errors
proxy.on('error', (err, req, res) => {
  console.error('Proxy error:', err.message);
  if (!res.headersSent) {
    res.writeHead(502, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ 
      error: 'Bad Gateway', 
      message: 'LitePolis backend not available. Start it with: python run_server.py'
    }));
  }
});

server.listen(PROXY_PORT, () => {
  console.log(`LitePolis E2E Proxy Server running at http://localhost:${PROXY_PORT}`);
  console.log(`Proxying /api/* to LitePolis at http://localhost:${LITEPOLIS_PORT}`);
  console.log(`Serving frontend from ${FRONTEND_BUILD_PATH}`);
  console.log('');
  console.log('To run E2E tests:');
  console.log(`  cd polis/e2e && CYPRESS_BASE_URL=http://localhost:${PROXY_PORT} npm test`);
});
