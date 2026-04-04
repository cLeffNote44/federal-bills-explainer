"use client";

import Link from "next/link";
import { Landmark, Menu, X, Bookmark, Bell, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/shared/theme-toggle";
import { useAuth } from "@/hooks/use-auth";
import { useUIStore } from "@/stores/ui-store";
import { useState } from "react";

const NAV_LINKS = [
  { href: "/", label: "Browse" },
  { href: "/topics", label: "Topics" },
  { href: "/saved", label: "Saved", auth: true, icon: Bookmark },
  { href: "/tracking", label: "Tracking", auth: true, icon: Bell },
];

export function Header() {
  const { user, loading, signOut } = useAuth();
  const openAuthModal = useUIStore((s) => s.openAuthModal);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 font-bold tracking-tight">
          <Landmark className="size-5 text-primary" />
          <span className="hidden sm:inline">Federal Bills Explainer</span>
          <span className="sm:hidden">FBX</span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden items-center gap-1 md:flex">
          {NAV_LINKS.map((link) => {
            if (link.auth && !user) return null;
            return (
              <Link key={link.href} href={link.href}>
                <Button variant="ghost" size="sm" className="gap-1.5">
                  {link.icon && <link.icon className="size-3.5" />}
                  {link.label}
                </Button>
              </Link>
            );
          })}
        </nav>

        {/* Right side */}
        <div className="flex items-center gap-1">
          <ThemeToggle />

          {!loading && (
            <>
              {user ? (
                <div className="hidden items-center gap-1 md:flex">
                  <Link href="/settings">
                    <Button variant="ghost" size="icon-sm">
                      <Settings className="size-3.5" />
                    </Button>
                  </Link>
                  <Button variant="outline" size="sm" onClick={() => signOut()}>
                    Sign Out
                  </Button>
                </div>
              ) : (
                <div className="hidden gap-1 md:flex">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => openAuthModal("login")}
                  >
                    Sign In
                  </Button>
                  <Button size="sm" onClick={() => openAuthModal("register")}>
                    Sign Up
                  </Button>
                </div>
              )}
            </>
          )}

          {/* Mobile menu toggle */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="size-4" /> : <Menu className="size-4" />}
          </Button>
        </div>
      </div>

      {/* Mobile nav */}
      {mobileOpen && (
        <div className="border-t border-border bg-background px-4 pb-4 pt-2 md:hidden">
          <nav className="flex flex-col gap-1">
            {NAV_LINKS.map((link) => {
              if (link.auth && !user) return null;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                >
                  <Button variant="ghost" size="sm" className="w-full justify-start gap-2">
                    {link.icon && <link.icon className="size-3.5" />}
                    {link.label}
                  </Button>
                </Link>
              );
            })}
            {user ? (
              <>
                <Link href="/settings" onClick={() => setMobileOpen(false)}>
                  <Button variant="ghost" size="sm" className="w-full justify-start gap-2">
                    <Settings className="size-3.5" />
                    Settings
                  </Button>
                </Link>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={() => {
                    signOut();
                    setMobileOpen(false);
                  }}
                >
                  Sign Out
                </Button>
              </>
            ) : (
              <div className="mt-2 flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1"
                  onClick={() => {
                    openAuthModal("login");
                    setMobileOpen(false);
                  }}
                >
                  Sign In
                </Button>
                <Button
                  size="sm"
                  className="flex-1"
                  onClick={() => {
                    openAuthModal("register");
                    setMobileOpen(false);
                  }}
                >
                  Sign Up
                </Button>
              </div>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}
