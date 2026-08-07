"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Fish, ActivitySquare, User, LogOut, Settings, X, CheckCircle2, Eye, EyeOff, Loader2 } from "lucide-react";
import { useAuth } from "./AuthProvider";
import { useState, useEffect } from "react";
import { fetchWithAuth } from "../lib/api";
import { supabase } from "@/lib/supabase";

export default function Navbar() {
  const pathname = usePathname();
  const { session, setSession } = useAuth();
  const [showFusionModal, setShowFusionModal] = useState(false);
  const [fusionUser, setFusionUser] = useState("");
  const [fusionPass, setFusionPass] = useState("");
  const [showFusionPass, setShowFusionPass] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isFusionConnected, setIsFusionConnected] = useState(false);
  const [savedFusionUsername, setSavedFusionUsername] = useState("");
  const [syncStatus, setSyncStatus] = useState<"idle" | "syncing" | "completed" | "error">("idle");
  useEffect(() => {
    if (session) {
      fetchWithAuth("/fusion-status")
        .then(res => res.json())
        .then(data => {
          if (data.connected) {
            setIsFusionConnected(true);
            setSavedFusionUsername(data.username || "");
          }
        })
        .catch(e => console.error("Failed to fetch fusion status", e));
    }
  }, [session]);

  const navItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Tank Profile", href: "/livestock", icon: Fish },
  ];

  const handleSaveFusion = async () => {
    setSyncStatus("syncing");
    try {
      const res = await fetchWithAuth("/update-fusion-credentials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fusion_username: fusionUser,
          fusion_password: fusionPass
        })
      });
      if (!res.ok) throw new Error("Failed response from server");
      
      // Kick off the background scraper
      const syncRes = await fetchWithAuth("/sync-fusion", { method: "POST" });
      const syncData = await syncRes.json();
      
      if (syncData.status !== "success" && syncData.status !== "skipped") {
        throw new Error(syncData.message || "Failed to start scraper");
      }
      
      // Simple and robust: Just check the database every 3 seconds to see if records arrived
      let attempts = 0;
      const pollInterval = setInterval(async () => {
        try {
          attempts++;
          const logsRes = await fetchWithAuth(`/get-logs?t=${Date.now()}`);
          const logsData = await logsRes.json();
          
          if (logsData && logsData.data && logsData.data.length > 0) {
            // Records found! The scraper finished.
            clearInterval(pollInterval);
            window.location.reload(); // Auto-reload the page
          }
          
          if (attempts > 60) {
            // Stop checking after 3 minutes (60 * 3s)
            clearInterval(pollInterval);
            alert("Sync timed out. Please refresh the page manually later.");
            setSyncStatus("idle");
            setShowFusionModal(false);
          }
        } catch (e) {
          console.error("Failed to check logs", e);
        }
      }, 3000);
      
    } catch (e: any) {
      alert(`Error starting sync: ${e.message || "Unknown error"}`);
      setSyncStatus("idle");
    }
  };

  const handleDisconnectFusion = async () => {
    if (confirm("Are you sure you want to disconnect Apex Fusion? This will stop pulling new data.")) {
      try {
        await fetchWithAuth("/disconnect-fusion", { method: "POST" });
        setIsFusionConnected(false);
        setSavedFusionUsername("");
        setShowFusionModal(false);
      } catch (e) {
        alert("Failed to disconnect.");
      }
    }
  };

  return (
    <>
      <nav className="h-14 bg-slate-900 border-b border-slate-800 flex items-center px-4 md:px-6 justify-between shrink-0">
        <div className="flex items-center gap-4 md:gap-8">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-cyan-600 rounded-lg flex items-center justify-center shrink-0">
              <ActivitySquare size={20} className="text-white" />
            </div>
            <h1 className="text-xl font-black text-cyan-400 tracking-tight drop-shadow-md hidden sm:block">
              Reef<span className="text-white">GPT</span>
            </h1>
          </Link>
          
          <div className="flex gap-2">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-1.5 md:px-4 md:py-2 rounded-full text-xs md:text-sm font-medium transition-all duration-300 ${
                    isActive 
                      ? "bg-cyan-600/20 text-cyan-400 border border-cyan-500/30 shadow-[0_0_15px_rgba(6,182,212,0.15)]" 
                      : "text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-transparent"
                  }`}
                >
                  <Icon size={16} className={isActive ? "text-cyan-400" : "text-slate-500"} /> 
                  <span className="hidden sm:inline">{item.name}</span>
                </Link>
              );
            })}
          </div>
        </div>

        {session && (
          <div className="flex items-center gap-2 md:gap-4">
            {isFusionConnected ? (
              <button
                onClick={() => setShowFusionModal(true)}
                className="text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 hover:bg-emerald-500/30 px-3 py-1.5 rounded-full transition-colors flex items-center gap-2"
              >
                <CheckCircle2 size={14} />
                <span className="hidden sm:inline">Apex Connected</span>
              </button>
            ) : (
              <button
                onClick={() => setShowFusionModal(true)}
                className="text-xs font-bold bg-orange-500/20 text-orange-400 border border-orange-500/50 hover:bg-orange-500/30 px-3 py-1.5 rounded-full transition-colors flex items-center gap-2"
              >
                <Settings size={14} />
                <span className="hidden sm:inline">Connect Apex</span>
              </button>
            )}
            
            <div className="flex items-center gap-2 text-xs font-medium bg-slate-800 px-3 py-1.5 rounded-full border border-slate-700 text-slate-300 hidden sm:flex">
              <User size={14} className="text-cyan-500" />
              {session.user?.email}
            </div>
            <button 
              onClick={async () => {
                await supabase.auth.signOut();
                setSession(null);
                window.location.reload();
              }}
              className="text-slate-400 hover:text-red-400 transition-colors"
              title="Log out"
            >
              <LogOut size={16} />
            </button>
          </div>
        )}
      </nav>

      {/* Apex Fusion Modal */}
      {showFusionModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 w-full max-w-md rounded-2xl p-6 shadow-2xl relative">
            {syncStatus !== "syncing" && (
              <button 
                onClick={() => setShowFusionModal(false)}
                className="absolute top-4 right-4 text-slate-400 hover:text-white"
              >
                <X size={20} />
              </button>
            )}
            
            {syncStatus === "syncing" && (
              <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
                <Loader2 size={48} className="text-cyan-400 animate-spin mb-6" />
                <h2 className="text-2xl font-black text-white mb-2">Syncing with Neptune...</h2>
                <p className="text-slate-400 text-sm leading-relaxed max-w-sm">
                  Our cloud scraper is securely logging in and pulling your latest telemetry data. 
                  This usually takes about 30 seconds.
                </p>
                <div className="w-full bg-slate-800 h-1.5 rounded-full mt-8 overflow-hidden">
                  <div className="bg-gradient-to-r from-cyan-500 to-blue-500 h-full animate-pulse w-full"></div>
                </div>
              </div>
            )}
            
            {syncStatus === "completed" && (
              <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
                <div className="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center mb-6 border border-emerald-500/30 shadow-[0_0_30px_rgba(16,185,129,0.3)]">
                  <CheckCircle2 size={32} className="text-emerald-400" />
                </div>
                <h2 className="text-2xl font-black text-white mb-2">Sync Finished!</h2>
                <p className="text-slate-400 text-sm leading-relaxed max-w-sm mb-8">
                  Your telemetry charts are ready. Refresh the dashboard to see your newly populated data!
                </p>
                <button 
                  onClick={() => window.location.reload()}
                  className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-lg transition-all shadow-lg shadow-emerald-900/50 hover:shadow-emerald-900/80 active:scale-95"
                >
                  Refresh Dashboard
                </button>
              </div>
            )}
            
            {syncStatus === "error" && (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <X size={48} className="text-red-500 mb-4" />
                <h2 className="text-xl font-bold text-white mb-2">Sync Failed</h2>
                <p className="text-slate-400 text-sm mb-6">There was an error syncing with Apex Fusion. Please try again.</p>
                <button onClick={() => setSyncStatus("idle")} className="w-full bg-slate-700 hover:bg-slate-600 py-2 rounded-lg text-white">
                  Try Again
                </button>
              </div>
            )}

            {syncStatus === "idle" && (
              isFusionConnected ? (
                <>
                  <h2 className="text-xl font-bold text-emerald-400 mb-2 flex items-center gap-2">
                    <CheckCircle2 size={24} /> Apex Connected
                  </h2>
                  <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 mb-6 mt-4">
                    <p className="text-sm text-slate-400 mb-1">Stored Fusion Account:</p>
                    <p className="text-base font-bold text-white">{savedFusionUsername}</p>
                  </div>
                  <p className="text-sm text-slate-400 mb-6 leading-relaxed">
                    Your Apex Fusion credentials are securely stored in the ReefGPT database. The cloud scraper will automatically sync your telemetry on demand.
                  </p>
                  <button 
                    onClick={handleDisconnectFusion}
                    className="w-full bg-slate-800 hover:bg-red-500/20 text-red-400 border border-red-500/30 hover:border-red-500/50 font-bold py-2 rounded-lg transition-colors"
                  >
                    Disconnect Apex
                  </button>
                </>
              ) : (
                <>
                  <h2 className="text-xl font-bold text-orange-400 mb-2">Connect Apex Fusion</h2>
                  <p className="text-sm text-slate-400 mb-6 leading-relaxed">
                    Neptune does not offer a public API. To pull your data automatically, our cloud scraper needs to log in to your Apex Fusion account. 
                    <br/><br/>
                    <strong className="text-red-400">Warning:</strong> Your credentials will be saved securely in the database so the scraper can run in the background.
                  </p>
  
                  <div className="space-y-4">
                    <div>
                      <label className="text-xs font-bold text-slate-300 uppercase block mb-1">Fusion Username</label>
                      <input 
                        type="text" 
                        autoComplete="off"
                        className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-white focus:border-orange-500 outline-none"
                        value={fusionUser}
                        onChange={e => setFusionUser(e.target.value)}
                      />
                    </div>
                    <div className="relative">
                      <label className="text-xs font-bold text-slate-300 uppercase block mb-1">Fusion Password</label>
                      <div className="relative">
                        <input 
                          type={showFusionPass ? "text" : "password"} 
                          autoComplete="new-password"
                          className="w-full bg-slate-950 border border-slate-800 rounded p-2 pr-10 text-white focus:border-orange-500 outline-none"
                          value={fusionPass}
                          onChange={e => setFusionPass(e.target.value)}
                        />
                        <button 
                          type="button"
                          onClick={() => setShowFusionPass(!showFusionPass)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                        >
                          {showFusionPass ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </div>
                    </div>
                    <button 
                      onClick={handleSaveFusion}
                      disabled={!fusionUser || !fusionPass}
                      className="w-full bg-orange-600 hover:bg-orange-500 text-white font-bold py-2 rounded-lg mt-4 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                      Connect & Sync
                    </button>
                  </div>
                </>
              )
            )}
          </div>
        </div>
      )}
    </>
  );
}
