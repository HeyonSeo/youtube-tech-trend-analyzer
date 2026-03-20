"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchAnalysis } from "@/lib/api";
import SummaryCards from "@/components/SummaryCards";
import KeywordRankingChart from "@/components/KeywordRankingChart";
import InterestRadarChart from "@/components/InterestRadarChart";
import VideoTable from "@/components/VideoTable";
import ExportButton from "@/components/ExportButton";
import RegionToggle from "@/components/RegionToggle";
import { CardSkeleton, ChartSkeleton, TableSkeleton } from "@/components/LoadingSkeleton";
import { Play } from "lucide-react";

export default function DashboardPage() {
  const [region, setRegion] = useState("all");
  const [periodDays, setPeriodDays] = useState(7);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["analysis", periodDays, region],
    queryFn: () => fetchAnalysis(periodDays, region),
    enabled: false,
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">대시보드</h1>
          <p className="text-slate-400 text-sm mt-1">
            YouTube 테크 트렌드를 분석합니다
          </p>
        </div>
        {data && <ExportButton periodDays={periodDays} region={region} />}
      </div>

      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <RegionToggle value={region} onChange={setRegion} />

        <div className="flex bg-[#1e293b] rounded-lg border border-slate-700 overflow-hidden">
          <button
            onClick={() => setPeriodDays(7)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              periodDays === 7
                ? "bg-blue-600 text-white"
                : "text-slate-400 hover:text-white hover:bg-slate-700"
            }`}
          >
            7일
          </button>
          <button
            onClick={() => setPeriodDays(30)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              periodDays === 30
                ? "bg-blue-600 text-white"
                : "text-slate-400 hover:text-white hover:bg-slate-700"
            }`}
          >
            30일
          </button>
        </div>

        <button
          onClick={() => refetch()}
          disabled={isLoading}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-5 py-2 rounded-lg font-medium transition-colors text-sm"
        >
          {isLoading ? (
            <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <Play className="w-4 h-4" />
          )}
          분석 시작
        </button>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 text-red-300 px-4 py-3 rounded-lg text-sm">
          {error instanceof Error ? error.message : "분석 중 오류가 발생했습니다."}
        </div>
      )}

      {isLoading && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <CardSkeleton key={i} />
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartSkeleton />
            <ChartSkeleton />
          </div>
          <TableSkeleton rows={5} />
        </div>
      )}

      {data && !isLoading && (
        <div className="space-y-6">
          <SummaryCards data={data} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <KeywordRankingChart keywords={data.keywords} />
            <InterestRadarChart interests={data.interests} />
          </div>

          <VideoTable videos={data.videos} />
        </div>
      )}

      {!data && !isLoading && !error && (
        <div className="flex flex-col items-center justify-center py-24 gap-4 text-slate-500">
          <Play className="w-16 h-16" />
          <p className="text-lg">위의 &quot;분석 시작&quot; 버튼을 클릭하여 트렌드를 분석하세요</p>
        </div>
      )}
    </div>
  );
}
