// Runtime config (overwritten at container start from API_BASE env)
//
// apiBase controls where /templates, /credits, etc. go:
//   ''     → same origin as the page (needs nginx or Firebase rewrites to the API)
//   'https://YOUR-BACKEND.run.app' → direct to Cloud Run backend (needs CORS; see backend app.py)
//
window.__CONFIG__ = {
  apiBase: 'http://localhost:5000',
  auth0Domain: 'dev-xiwa5ogu3vfhcfba.us.auth0.com',
  auth0ClientId: 'glHmYjs0pbowPZAtSKaQty4VJjvJnQgO',
  generateModes: [
    { value: 'zturbo', label: 'Japanese' },
    { value: 'uso',    label: 'Oil Painting' },
  ],
};
