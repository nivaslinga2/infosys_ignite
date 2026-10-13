// In development (Vite dev server on :5173), target the FastAPI backend at http://localhost:8000
// In production deployment (single container or same origin), use relative root "" or VITE_API_BASE
export const API_BASE = 
  import.meta.env.VITE_API_BASE ||
  (typeof window !== 'undefined' && window.location.port === '5173' ? 'http://localhost:8000' : '');
