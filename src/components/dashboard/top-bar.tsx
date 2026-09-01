"use client";

import { Bell, Search, Zap } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/Avatar";
import Link from "next/link";

export function TopBar() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-white/5 bg-surface-dark/50 px-4 sm:px-6">
      {/* Mobile logo */}
      <div className="flex items-center gap-3">
        <Link href="/" className="flex lg:hidden items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-viral-purple to-viral-pink">
            <Zap className="h-4 w-4 text-white" />
          </div>
        </Link>
        <h1 className="text-lg font-semibold hidden sm:block">Dashboard</h1>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">
        {/* Search */}
        <button className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-muted-foreground hover:bg-white/10 transition-colors">
          <Search className="h-4 w-4" />
          <span className="hidden sm:inline">Search...</span>
          <kbd className="hidden sm:inline-flex h-5 items-center rounded border border-white/10 px-1.5 text-[10px] text-muted-foreground">
            ⌘K
          </kbd>
        </button>

        {/* Notifications */}
        <button className="relative rounded-xl p-2 text-muted-foreground hover:bg-white/5 hover:text-foreground transition-colors">
          <Bell className="h-4 w-4" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-viral-pink" />
        </button>

        {/* Avatar */}
        <Avatar className="h-8 w-8 border border-white/10">
          <AvatarFallback className="bg-gradient-to-br from-viral-purple to-viral-pink text-white text-xs font-medium">
            VC
          </AvatarFallback>
        </Avatar>
      </div>
    </header>
  );
}
