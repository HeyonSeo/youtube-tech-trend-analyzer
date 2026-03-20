"use client";

import { useSession, signOut } from "next-auth/react";
import Link from "next/link";
import { useState, useRef, useEffect } from "react";

export default function UserMenu() {
  const { data: session, status } = useSession();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (status === "loading") {
    return (
      <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-slate-700 animate-pulse" />
    );
  }

  if (!session?.user) {
    return (
      <Link
        href="/login"
        className="px-3 py-2 rounded-lg text-sm font-medium text-gray-600 dark:text-slate-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
      >
        로그인
      </Link>
    );
  }

  const user = session.user;
  const role = (user as any).role || "member";
  const initial = (user.name || user.email || "U")[0].toUpperCase();

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
      >
        <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-bold">
          {initial}
        </div>
        <span className="hidden sm:inline text-sm font-medium text-gray-700 dark:text-slate-200">
          {user.name || user.email}
        </span>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-[#1e293b] rounded-xl shadow-lg border border-gray-200 dark:border-[#334155] py-2 z-50">
          <div className="px-4 py-3 border-b border-gray-100 dark:border-[#334155]">
            <p className="text-sm font-medium text-gray-900 dark:text-slate-100">
              {user.name || "사용자"}
            </p>
            <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">
              {user.email}
            </p>
            <span
              className={`inline-block mt-2 px-2 py-0.5 rounded text-xs font-medium ${
                role === "admin"
                  ? "bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300"
                  : "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
              }`}
            >
              {role === "admin" ? "Admin" : "Member"}
            </span>
          </div>
          <button
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
          >
            로그아웃
          </button>
        </div>
      )}
    </div>
  );
}
