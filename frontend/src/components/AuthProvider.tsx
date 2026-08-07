"use client";
import { useState, useEffect, createContext, useContext } from "react";
import { Auth } from "@supabase/auth-ui-react";
import { ThemeSupa } from "@supabase/auth-ui-shared";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_KEY!
);

export const AuthContext = createContext<any>(null);

export function useAuth() {
  return useContext(AuthContext);
}

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  // Intercept all fetches to inject the user ID
  if (session && typeof window !== "undefined") {
    const originalFetch = window.fetch;
    // Prevent attaching multiple times if re-rendered
    if (!(window as any)._fetchIntercepted) {
      window.fetch = async function () {
        let [resource, config] = arguments;
        if (!config) config = {};
        if (!config.headers) config.headers = {};
        
        // Handle both Headers object and plain record
        if (config.headers instanceof Headers) {
          config.headers.set("x-user-id", session.user.id);
        } else {
          config.headers["x-user-id"] = session.user.id;
        }
        
        return originalFetch(resource, config);
      };
      (window as any)._fetchIntercepted = true;
    }
  }

  if (loading) return <div className="h-screen flex items-center justify-center bg-slate-950 text-white">Loading...</div>;

  if (!session) {
    return (
      <div className="flex items-center justify-center h-screen w-full bg-slate-950 flex-col gap-8 overflow-y-auto py-10">
        <div className="w-full max-w-md bg-slate-900 p-8 rounded-xl border border-slate-800 shadow-2xl shrink-0 mt-10">
          <h1 className="text-3xl text-blue-400 font-bold mb-2 text-center tracking-tight">ReefOS</h1>
          <p className="text-slate-400 text-center mb-8">Sign in to your tank dashboard</p>
          <Auth 
            supabaseClient={supabase} 
            appearance={{
              theme: ThemeSupa,
              variables: {
                default: {
                  colors: {
                    brand: '#3b82f6',
                    brandAccent: '#2563eb',
                    messageText: '#cbd5e1',
                    inputText: 'white',
                    inputBackground: 'rgba(0,0,0,0.5)',
                    inputBorder: 'rgba(255,255,255,0.1)',
                    inputBorderHover: 'rgba(59,130,246,0.5)',
                    inputBorderFocus: '#3b82f6',
                    anchorTextColor: '#60a5fa',
                    dividerBackground: 'rgba(255,255,255,0.1)',
                  },
                  space: {
                    buttonPadding: '12px 16px',
                    inputPadding: '12px 16px',
                  },
                  borderWidths: {
                    buttonBorderWidth: '1px',
                    inputBorderWidth: '1px',
                  },
                  radii: {
                    borderRadiusButton: '12px',
                    buttonBorderRadius: '12px',
                    inputBorderRadius: '12px',
                  },
                },
              },
              className: {
                container: 'auth-container',
                button: 'auth-button hover:shadow-[0_0_15px_rgba(59,130,246,0.5)] transition-shadow duration-300',
                input: 'auth-input backdrop-blur-md',
                message: 'text-slate-300',
                anchor: 'text-blue-400 hover:text-blue-300 transition-colors',
                divider: 'bg-white/10',
                label: 'text-slate-300 font-medium',
              },
            }}
            theme="dark"
            providers={[]} 
          />
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ session, setSession }}>
      {children}
    </AuthContext.Provider>
  );
}
