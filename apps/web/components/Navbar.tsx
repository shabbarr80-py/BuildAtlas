"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { LogOut, Menu, X } from "lucide-react";
import { logout } from "@/lib/api";

export default function Navbar() {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setAuthed(!!window.localStorage.getItem("buildatlas_token"));
  }, []);

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // Ignore logout errors; always clear local state and redirect.
    }
    window.localStorage.removeItem("buildatlas_token");
    setAuthed(false);
    setOpen(false);
    window.location.href = "/";
  }

  const links = authed
    ? [
        { href: "/dashboard", label: "Dashboard" },
        { href: "/profile", label: "Profile" },
        { href: "/settings", label: "Settings" },
      ]
    : [
        { href: "/login", label: "Sign in" },
        { href: "/register", label: "Create account" },
      ];

  return (
    <nav className="sticky top-0 z-20 border-b border-line bg-graphite/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
        <Link
          href="/"
          className="flex items-center gap-2 font-semibold tracking-tight"
        >
          <span className="grid h-6 w-6 place-items-center bg-sunshine text-graphite">
            <span className="text-[10px]">B</span>
          </span>
          buildatlas
        </Link>
        <div className="hidden md:flex items-center gap-6 text-sm">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-muted hover:text-cloud transition"
            >
              {link.label}
            </Link>
          ))}
          {authed && (
            <button
              onClick={handleLogout}
              className="border border-line px-3 py-1.5 text-sm text-muted hover:bg-panel transition"
            >
              Sign out
            </button>
          )}
        </div>
        <button
          onClick={() => setOpen(!open)}
          className="md:hidden text-muted"
          aria-label="Toggle navigation"
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>
      {open && (
        <div className="md:hidden border-t border-line bg-graphite p-4">
          <div className="space-y-3">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className="block px-3 py-2 text-sm text-muted hover:bg-panel hover:text-cloud rounded transition"
              >
                {link.label}
              </Link>
            ))}
            {authed && (
              <button
                onClick={handleLogout}
                className="block w-full text-left border border-line px-3 py-2 text-sm text-muted hover:bg-panel rounded transition"
              >
                Sign out
              </button>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
