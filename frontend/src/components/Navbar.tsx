"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Fish, ActivitySquare, User, LogOut } from "lucide-react";
import { useAuth } from "./AuthProvider";

export default function Navbar() {
  const pathname = usePathname();
  const { session, setSession } = useAuth();

  const navItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Tank Profile", href: "/livestock", icon: Fish },
  ];

  return (
    <nav className="h-14 bg-slate-900 border-b border-slate-800 flex items-center px-6 justify-between shrink-0">
      <div className="flex items-center gap-8">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-cyan-600 rounded-lg flex items-center justify-center">
            <ActivitySquare size={20} className="text-white" />
          </div>
          <h1 className="text-xl font-black text-cyan-400 tracking-tight drop-shadow-md">
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
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 ${
                  isActive 
                    ? "bg-cyan-600/20 text-cyan-400 border border-cyan-500/30 shadow-[0_0_15px_rgba(6,182,212,0.15)]" 
                    : "text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-transparent"
                }`}
              >
                <Icon size={16} className={isActive ? "text-cyan-400" : "text-slate-500"} /> 
                {item.name}
              </Link>
            );
          })}
        </div>
      </div>

      {session && (
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-xs font-medium bg-slate-800 px-3 py-1.5 rounded-full border border-slate-700 text-slate-300">
            <User size={14} className="text-cyan-500" />
            {session.user?.email || "Test Account"}
          </div>
          <button 
            onClick={() => setSession(null)}
            className="text-slate-400 hover:text-red-400 transition-colors"
            title="Log out"
          >
            <LogOut size={16} />
          </button>
        </div>
      )}
    </nav>
  );
}
