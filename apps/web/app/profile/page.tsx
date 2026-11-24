"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Mail, User as UserIcon } from "lucide-react";
import { me, logout, User } from "@/lib/api";

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    void me()
      .then(setUser)
      .catch((reason: unknown) => {
        setError(
          reason instanceof Error ? reason.message : "Unable to load profile",
        );
      })
      .finally(() => setLoading(false));
  }, []);

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // Ignore logout errors; always clear local state and redirect.
    }
    window.localStorage.removeItem("buildatlas_token");
    window.location.href = "/";
  }

  if (loading) {
    return (
      <main className="mx-auto min-h-screen max-w-3xl px-6 py-12">
        <Link href="/dashboard" className="text-sm text-muted">
          ← Dashboard
        </Link>
        <p role="status" className="mt-8 border border-line p-6 text-muted">
          Loading your profile...
        </p>
      </main>
    );
  }

  if (error || !user) {
    return (
      <main className="mx-auto min-h-screen max-w-3xl px-6 py-12">
        <Link href="/dashboard" className="text-sm text-muted">
          ← Dashboard
        </Link>
        <p role="alert" className="mt-8 border border-red-500/40 p-4 text-red-300">
          {error} Please sign in again.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto min-h-screen max-w-3xl px-6 py-12">
      <Link href="/dashboard" className="text-sm text-muted">
        ← Dashboard
      </Link>
      <div className="mt-10 border border-line bg-panel p-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="grid h-12 w-12 place-items-center rounded-xl bg-sunshine text-graphite font-bold">
            <UserIcon size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-semibold">Profile</h1>
            <p className="text-sm text-muted">BuildAtlas account</p>
          </div>
        </div>
        <dl className="grid gap-4">
          <div className="border-b border-line pb-2">
            <dt className="text-xs uppercase tracking-[.16em] text-muted">
              Email
            </dt>
            <dd className="mt-1 text-sm">{user.email}</dd>
          </div>
          <div className="border-b border-line pb-2">
            <dt className="text-xs uppercase tracking-[.16em] text-muted">
              Account ID
            </dt>
            <dd className="mt-1 text-sm text-muted truncate">{user.id}</dd>
          </div>
        </dl>
        <div className="mt-8">
          <button
            onClick={handleLogout}
            className="border border-line px-4 py-2 text-sm hover:bg-panel transition"
          >
            <Mail size={16} className="mr-2 inline" /> Sign out
          </button>
        </div>
      </div>
    </main>
  );
}
