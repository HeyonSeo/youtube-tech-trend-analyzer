"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchTrends, TrendItem } from "@/lib/api";
import RegionToggle from "@/components/RegionToggle";
import { TableSkeleton, ChartSkeleton } from "@/components/LoadingSkeleton";
import TrendModal from "@/components/TrendModal";
import { Play } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const WEEKS_OPTIONS = [2, 4, 8, 12] as const;

const CATEGORY_COLORS: Record<string, string> = {
  Language: "bg-blue-500/20 text-blue-400",
  Framework: "bg-purple-500/20 text-purple-400",
  Tool: "bg-amber-500/20 text-amber-400",
  Platform: "bg-emerald-500/20 text-emerald-400",
  Database: "bg-rose-500/20 text-rose-400",
  AI: "bg-cyan-500/20 text-cyan-400",
  Cloud: "bg-indigo-500/20 text-indigo-400",
  DevOps: "bg-orange-500/20 text-orange-400",
};

function getCategoryStyle(category: string) {
  return CATEGORY_COLORS[category] || "bg-slate-500/20 text-slate-400";
}

function RankChange({ item }: { item: TrendItem }) {
  if (item.is_new) {
    return (
      <span className="inline-flex items-center gap-1 text-xs font-medium text-green-400 bg-green-500/20 px-2 py-0.5 rounded-full">
        🆕 신규
      </span>
    );
  }

  const change = item.rank_change;
  if (change === null) {
    return <span className="text-slate-500">—</span>;
  }
  if (change > 0) {
    return <span className="text-green-400 font-medium">▲ {change}</span>;
  }
  if (change < 0) {
    return <span className="text-red-400 font-medium">▼ {Math.abs(change)}</span>;
  }
  return <span className="text-slate-500">— 0</span>;
}

export default function TrendsPage() {
  const [region, setRegion] = useState("all");
  const [weeks, setWeeks] = useState<number>(2);
  const [modalKeyword, setModalKeyword] = useState<string | null>(null);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["trends", region, weeks],
    queryFn: () => fetchTrends(region, weeks),
    enabled: false,
  });

  const chartData = data?.trends.map((t) => ({
    keyword: t.keyword,
    count: t.count,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">트렌드 비교</h1>
        <p className="text-slate-400 text-sm mt-1">
          키워드 순위 변동과 트렌드를 비교합니다
        </p>
      </div>

      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <RegionToggle value={region} onChange={setRegion} />

        <div className="flex bg-[#1e293b] rounded-lg border border-slate-700 overflow-hidden">
          {WEEKS_OPTIONS.map((w) => (
            <button
              key={w}
              onClick={() => setWeeks(w)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                weeks === w
                  ? "bg-blue-600 text-white"
                  : "text-slate-400 hover:text-white hover:bg-slate-700"
              }`}
            >
              {w}주
            </button>
          ))}
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
          트렌드 조회
        </button>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 text-red-300 px-4 py-3 rounded-lg text-sm">
          {error instanceof Error ? error.message : "트렌드 조회 중 오류가 발생했습니다."}
        </div>
      )}

      {isLoading && (
        <div className="space-y-6">
          <TableSkeleton rows={10} />
          <ChartSkeleton />
        </div>
      )}

      {data && !isLoading && (
        <div className="space-y-6">
          <div className="text-sm text-slate-400">
            비교 기간: {data.previous_date} → {data.current_date}
          </div>

          {/* Trend Table */}
          <div className="bg-[#1e293b] rounded-xl border border-[#334155] overflow-hidden">
            <div className="px-6 py-4 border-b border-[#334155]">
              <h2 className="text-base font-semibold text-white">키워드 순위</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#334155] text-slate-400 text-left">
                    <th className="px-6 py-3 font-medium">순위</th>
                    <th className="px-6 py-3 font-medium">키워드</th>
                    <th className="px-6 py-3 font-medium">빈도</th>
                    <th className="px-6 py-3 font-medium">카테고리</th>
                    <th className="px-6 py-3 font-medium">변동</th>
                  </tr>
                </thead>
                <tbody>
                  {data.trends.map((item) => (
                    <tr
                      key={item.keyword}
                      onClick={() => setModalKeyword(item.keyword)}
                      className="border-b border-[#334155] hover:bg-[#334155]/30 cursor-pointer transition-colors"
                    >
                      <td className="px-6 py-3 text-slate-300 font-mono">{item.rank}</td>
                      <td className="px-6 py-3 text-white font-medium">{item.keyword}</td>
                      <td className="px-6 py-3 text-slate-300">{item.count}</td>
                      <td className="px-6 py-3">
                        <span
                          className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full ${getCategoryStyle(item.category)}`}
                        >
                          {item.category}
                        </span>
                      </td>
                      <td className="px-6 py-3">
                        <RankChange item={item} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Trend Line Chart */}
          <div className="bg-[#1e293b] rounded-xl p-6 border border-[#334155]">
            <h2 className="text-base font-semibold text-white mb-4">키워드 빈도 비교</h2>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="keyword"
                  stroke="#94a3b8"
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  angle={-30}
                  textAnchor="end"
                  height={60}
                />
                <YAxis
                  stroke="#94a3b8"
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1e293b",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                    color: "#f1f5f9",
                  }}
                />
                <Legend wrapperStyle={{ color: "#94a3b8" }} />
                <Line
                  type="monotone"
                  dataKey="count"
                  name="빈도"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: "#3b82f6", r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {!data && !isLoading && !error && (
        <div className="flex flex-col items-center justify-center py-24 gap-4 text-slate-500">
          <Play className="w-16 h-16" />
          <p className="text-lg">위의 &quot;트렌드 조회&quot; 버튼을 클릭하여 트렌드를 조회하세요</p>
        </div>
      )}

      {modalKeyword && (
        <TrendModal
          keyword={modalKeyword}
          isOpen={true}
          onClose={() => setModalKeyword(null)}
        />
      )}
    </div>
  );
}
