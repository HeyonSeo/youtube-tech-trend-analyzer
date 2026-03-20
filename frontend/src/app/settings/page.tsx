"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchSettings, clearCache } from "@/lib/api";
import { Settings, Search, Grid3X3, Database, Key, Info, Trash2 } from "lucide-react";

const CATEGORY_COLORS = [
  "bg-blue-500",
  "bg-emerald-500",
  "bg-violet-500",
  "bg-amber-500",
  "bg-rose-500",
  "bg-cyan-500",
  "bg-orange-500",
  "bg-pink-500",
];

function formatTTL(seconds: number): string {
  if (seconds >= 3600) {
    const hours = Math.floor(seconds / 3600);
    return `${hours}시간`;
  }
  if (seconds >= 60) {
    const minutes = Math.floor(seconds / 60);
    return `${minutes}분`;
  }
  return `${seconds}초`;
}

export default function SettingsPage() {
  const [clearing, setClearing] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["settings"],
    queryFn: fetchSettings,
    enabled: true,
  });

  const handleClearCache = async () => {
    setClearing(true);
    setToast(null);
    try {
      await clearCache();
      setToast({ type: "success", message: "캐시가 성공적으로 초기화되었습니다." });
    } catch {
      setToast({ type: "error", message: "캐시 초기화에 실패했습니다." });
    } finally {
      setClearing(false);
      setTimeout(() => setToast(null), 3000);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Settings className="w-6 h-6" />
          설정
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          애플리케이션 설정을 확인합니다
        </p>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 text-red-300 px-4 py-3 rounded-lg text-sm">
          {error instanceof Error ? error.message : "설정을 불러오는 중 오류가 발생했습니다."}
        </div>
      )}

      {isLoading && (
        <div className="space-y-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-[#1e293b] rounded-xl border border-slate-700 p-6 animate-pulse">
              <div className="h-5 bg-slate-700 rounded w-32 mb-4" />
              <div className="h-4 bg-slate-700 rounded w-64" />
            </div>
          ))}
        </div>
      )}

      {toast && (
        <div
          className={`px-4 py-3 rounded-lg text-sm ${
            toast.type === "success"
              ? "bg-emerald-900/30 border border-emerald-700 text-emerald-300"
              : "bg-red-900/30 border border-red-700 text-red-300"
          }`}
        >
          {toast.message}
        </div>
      )}

      {data && !isLoading && (
        <div className="space-y-6">
          {/* 검색어 설정 */}
          <div className="bg-[#1e293b] rounded-xl border border-slate-700 p-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
              <Search className="w-5 h-5 text-blue-400" />
              검색어 설정
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-medium text-slate-300 mb-3">한국어 검색어</h3>
                <div className="flex flex-wrap gap-2">
                  {data.search_queries.kr.map((q) => (
                    <span
                      key={q}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-900/40 text-blue-300 border border-blue-700/50"
                    >
                      {q}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-slate-300 mb-3">영어 검색어</h3>
                <div className="flex flex-wrap gap-2">
                  {data.search_queries.en.map((q) => (
                    <span
                      key={q}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-emerald-900/40 text-emerald-300 border border-emerald-700/50"
                    >
                      {q}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            <div className="mt-4 flex items-start gap-2 text-slate-500 text-sm">
              <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>검색어를 변경하려면 서버의 queries.json 파일을 수정하세요</span>
            </div>
          </div>

          {/* 관심사 카테고리 */}
          <div className="bg-[#1e293b] rounded-xl border border-slate-700 p-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
              <Grid3X3 className="w-5 h-5 text-violet-400" />
              관심사 카테고리
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {data.categories.map((cat, i) => (
                <div
                  key={cat}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/50 border border-slate-700"
                >
                  <span className={`w-3 h-3 rounded-full ${CATEGORY_COLORS[i % CATEGORY_COLORS.length]}`} />
                  <span className="text-sm font-medium text-slate-200">{cat}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 캐시 설정 */}
          <div className="bg-[#1e293b] rounded-xl border border-slate-700 p-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
              <Database className="w-5 h-5 text-amber-400" />
              캐시 설정
            </h2>
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="text-sm text-slate-300">
                현재 캐시 TTL: <span className="font-semibold text-white">{formatTTL(data.cache_ttl_seconds)}</span>
              </div>
              <button
                onClick={handleClearCache}
                disabled={clearing}
                className="flex items-center gap-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-medium transition-colors text-sm"
              >
                {clearing ? (
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                ) : (
                  <Trash2 className="w-4 h-4" />
                )}
                캐시 초기화
              </button>
            </div>
          </div>

          {/* API 키 */}
          <div className="bg-[#1e293b] rounded-xl border border-slate-700 p-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
              <Key className="w-5 h-5 text-rose-400" />
              API 키
            </h2>
            <div className="flex items-center gap-3 mb-3">
              <code className="px-3 py-1.5 bg-slate-800 rounded-lg text-slate-400 text-sm font-mono tracking-widest">
                {"••••••••••••••••"}
              </code>
            </div>
            <div className="flex items-start gap-2 text-slate-500 text-sm">
              <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>API 키는 서버 환경변수에서 관리됩니다</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
