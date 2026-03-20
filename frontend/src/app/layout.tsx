import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import QueryProvider from "@/lib/QueryProvider";
import ErrorBoundary from "@/components/ErrorBoundary";
import ThemeToggle from "@/components/ThemeToggle";
import AuthProvider from "@/components/AuthProvider";
import UserMenu from "@/components/UserMenu";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "TechPulse — 테크 트렌드 분석기",
  description: "YouTube 기반 기술 트렌드 분석 대시보드",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className={`${inter.className} antialiased bg-gray-50 text-gray-900 dark:bg-[#0f172a] dark:text-gray-100 min-h-screen`}>
        <nav className="sticky top-0 z-50 bg-white/95 dark:bg-[#0f172a]/95 backdrop-blur-sm border-b border-gray-200 dark:border-[#334155]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-8">
                <Link href="/" className="text-xl font-bold text-blue-400 tracking-tight">
                  TechPulse
                </Link>
                <div className="hidden sm:flex items-center gap-1">
                  <Link
                    href="/"
                    className="px-3 py-2 rounded-lg text-sm font-medium text-gray-600 dark:text-slate-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    대시보드
                  </Link>
                  <Link
                    href="/keywords"
                    className="px-3 py-2 rounded-lg text-sm font-medium text-gray-600 dark:text-slate-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    키워드
                  </Link>
                  <Link
                    href="/videos"
                    className="px-3 py-2 rounded-lg text-sm font-medium text-gray-600 dark:text-slate-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    영상
                  </Link>
                  <Link
                    href="/trends"
                    className="px-3 py-2 rounded-lg text-sm font-medium text-gray-600 dark:text-slate-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    트렌드
                  </Link>
                  <Link
                    href="/settings"
                    className="px-3 py-2 rounded-lg text-sm font-medium text-gray-600 dark:text-slate-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    설정
                  </Link>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <ThemeToggle />
                <UserMenu />
              </div>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <AuthProvider>
            <QueryProvider>
              <ErrorBoundary>
                {children}
              </ErrorBoundary>
            </QueryProvider>
          </AuthProvider>
        </main>
      </body>
    </html>
  );
}
