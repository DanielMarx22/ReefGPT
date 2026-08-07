"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import { useRouter } from "next/navigation";
import { Waves, Eye, EyeOff, Mail, Lock } from "lucide-react";

type AuthMode = "signin" | "signup" | "reset";

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<AuthMode>("signin");
  
  // Form State
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    // Check if user is already logged in
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        router.push("/");
      } else {
        setLoading(false);
      }
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        router.push("/");
      }
    });

    return () => subscription.unsubscribe();
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");
    setIsSubmitting(true);

    try {
      if (mode === "signup") {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
        });
        if (error) {
          // If "Prevent Email Enumeration" is OFF in Supabase, we can catch "User already registered" here.
          if (error.message.includes("User already registered") || error.message.includes("already registered")) {
            throw new Error("This email already has an account. Please sign in instead.");
          }
          throw error;
        }
        
        // Supabase returns a user immediately if email confirmations are disabled, 
        // or a session is null if they are enabled.
        if (data.session) {
          router.push("/");
        } else {
          setSuccessMsg("Check your email for the confirmation link!");
        }

      } else if (mode === "signin") {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) {
          if (error.message.includes("Invalid login")) {
            throw new Error("Invalid email or password.");
          }
          throw error;
        }
        // onAuthStateChange will handle redirect

      } else if (mode === "reset") {
        const { error } = await supabase.auth.resetPasswordForEmail(email, {
          redirectTo: `${window.location.origin}/update-password`,
        });
        if (error) throw error;
        setSuccessMsg("If an account exists, a password reset link has been sent to your email.");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "An unexpected error occurred.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1582967788606-a171c1080cb0?q=80&w=3174&auto=format&fit=crop')] bg-cover bg-center opacity-20"></div>
      
      <div className="w-full max-w-md relative z-10 bg-slate-900/80 backdrop-blur-xl border border-white/10 p-8 rounded-3xl shadow-2xl">
        <div className="flex flex-col items-center mb-8">
          <div className="bg-blue-500/20 p-4 rounded-2xl mb-4 border border-blue-500/30 shadow-[0_0_30px_rgba(59,130,246,0.3)]">
            <Waves className="w-10 h-10 text-blue-400" />
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-br from-white to-slate-400 bg-clip-text text-transparent">
            ReefGPT
          </h1>
          <p className="text-slate-400 text-sm mt-2">
            {mode === "signin" && "Log in to manage your aquarium."}
            {mode === "signup" && "Create a new account."}
            {mode === "reset" && "Reset your password."}
          </p>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-xl text-red-400 text-sm">
            {errorMsg}
          </div>
        )}
        
        {successMsg && (
          <div className="mb-4 p-3 bg-green-500/10 border border-green-500/50 rounded-xl text-green-400 text-sm">
            {successMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Email</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Mail className="h-5 w-5 text-slate-500" />
              </div>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="block w-full pl-10 pr-3 py-3 border border-white/10 rounded-xl bg-black/50 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                placeholder="you@example.com"
              />
            </div>
          </div>

          {mode !== "reset" && (
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-slate-500" />
                </div>
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-10 pr-10 py-3 border border-white/10 rounded-xl bg-black/50 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 focus:ring-offset-slate-900 transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-6"
          >
            {isSubmitting ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            ) : mode === "signin" ? (
              "Sign In"
            ) : mode === "signup" ? (
              "Sign Up"
            ) : (
              "Send Reset Link"
            )}
          </button>
        </form>

        <div className="mt-6 flex flex-col space-y-3 text-center text-sm">
          {mode === "signin" && (
            <>
              <button onClick={() => setMode("reset")} className="text-blue-400 hover:text-blue-300 transition-colors">
                Forgot your password?
              </button>
              <button onClick={() => setMode("signup")} className="text-slate-400 hover:text-white transition-colors">
                Don't have an account? <span className="text-blue-400">Sign up</span>
              </button>
            </>
          )}
          {mode === "signup" && (
            <button onClick={() => setMode("signin")} className="text-slate-400 hover:text-white transition-colors">
              Already have an account? <span className="text-blue-400">Sign in</span>
            </button>
          )}
          {mode === "reset" && (
            <button onClick={() => setMode("signin")} className="text-slate-400 hover:text-white transition-colors">
              Back to <span className="text-blue-400">Sign in</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
