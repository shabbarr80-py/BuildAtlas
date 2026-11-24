"use client";

import Link from "next/link";
import { useState } from "react";
import { LogOut, Settings as SettingsIcon } from "lucide-react";
import { logout } from "@/lib/api";

export default function SettingsPage() {
  async function handleLogout() {
    try {
      await logout();
    } catch {
      // Ignore logout errors; always clear local state and redirect.
    }
    window.localStorage.removeItem("buildatlas_token");
    window.location.href = "/";
  }

  return (
    <main className="mx-auto min-h-screen max-w-3xl px-6 py-12">
      <Link href="/dashboard" className="text-sm text-muted">
        ← Dashboard
      </Link>
      <div className="mt-10 border border-line bg-panel p-8">
        <div className="flex items-center gap-4 mb-6">
          <SettingsIcon size={20} className="text-sunshine" />
          <div>
            <h1 className="text-2xl font-semibold">Settings</h1>
            <p className="text-sm text-muted">Application configuration</p>
          </div>
        </div>
        <div className="space-y-4">
          <div className="border border-line rounded-lg p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium">API endpoint</p>
                <p className="text-xs text-muted truncate max-w-xs">
                  {typeof window === "undefined"
                    ? ""
                    : (process.env.NEXT_PUBLIC_API_URL ??
                        "http://localhost:8000/api/v1")}
                </p>
              </div>
            </div>
          </div>
          <div className="border-t border-line pt-6">
            <button
              onClick={handleLogout}
              className="border border-red-500/40 text-red-300 px-4 py-2 text-sm hover:bg-red-500/10 transition"
            >
              <LogOut size={16} className="mr-2 inline" /> Sign out
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
