import { supabase } from './supabase';

// Dynamically route to local backend if developing locally, otherwise hit production
const getApiBase = () => {
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    // If accessing via localhost or local network (e.g., from your phone)
    if (host === 'localhost' || host.startsWith('192.168.') || host.startsWith('10.')) {
      return `http://${host}:8000`; // Hit the local uvicorn server
    }
  }
  // Otherwise, use the explicit env var or default to production
  return process.env.NEXT_PUBLIC_API_URL || "https://reefgpt.onrender.com";
};

const API_BASE = getApiBase();
export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const { data: { session } } = await supabase.auth.getSession();
  
  const headers = new Headers(options.headers || {});
  if (session?.user?.id) {
    headers.set('x-user-id', session.user.id);
  }

  // Ensure endpoint starts with / or is full URL
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  return fetch(url, {
    ...options,
    headers,
  });
}
