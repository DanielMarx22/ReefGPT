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
                        }
                    }
                }
            }} 
            providers={[]} 
          />
        </div>
        
        {/* DEV BYPASS */}
        <div className="w-full max-w-md bg-slate-900 p-4 rounded-xl border border-dashed border-slate-700 shrink-0 mb-10">
          <p className="text-slate-400 text-center mb-4 text-sm font-semibold">Developer Testing Scenarios</p>
          <div className="flex flex-col gap-2">
            <button onClick={() => setSession({ user: { id: "00000000-0000-0000-0000-000000000000", email: "personal@reef.local" }})} className="bg-sky-900/50 hover:bg-sky-900/70 text-sky-400 p-2 rounded transition-colors text-sm font-bold border border-sky-800 cursor-pointer mb-2">Login as Personal Account</button>
            <button onClick={() => setSession({ user: { id: "11111111-1111-1111-1111-111111111111", email: "alk_spike@test.com" }})} className="bg-red-900/50 hover:bg-red-900/70 text-red-400 p-2 rounded transition-colors text-sm font-medium cursor-pointer">Customer A: Alk & Calc Spike</button>
            <button onClick={() => setSession({ user: { id: "22222222-2222-2222-2222-222222222222", email: "amino_toxicity@test.com" }})} className="bg-orange-900/50 hover:bg-orange-900/70 text-orange-400 p-2 rounded transition-colors text-sm font-medium cursor-pointer">Customer B: Amino Overdose</button>
            <button onClick={() => setSession({ user: { id: "33333333-3333-3333-3333-333333333333", email: "rogue_fish@test.com" }})} className="bg-green-900/50 hover:bg-green-900/70 text-green-400 p-2 rounded transition-colors text-sm font-medium cursor-pointer">Customer C: Rogue Fish (Nipping)</button>
            <button onClick={() => setSession({ user: { id: "44444444-4444-4444-4444-444444444444", email: "heater_failure@test.com" }})} className="bg-blue-900/50 hover:bg-blue-900/70 text-blue-400 p-2 rounded transition-colors text-sm font-medium cursor-pointer">Customer D: Heater Failure</button>
            <button onClick={() => setSession({ user: { id: "55555555-5555-5555-5555-555555555555", email: "alk_depletion@test.com" }})} className="bg-purple-900/50 hover:bg-purple-900/70 text-purple-400 p-2 rounded transition-colors text-sm font-medium cursor-pointer">Customer E: Alk Depletion</button>
          </div>
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
