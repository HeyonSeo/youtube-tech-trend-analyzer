"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchKeywordHistory } from "@/lib/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { X } from "lucide-react";

interface TrendModalProps {
  keyword: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function TrendModal({ keyword, isOpen, onClose }: TrendModalProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["keywordHistory", keyword],
    queryFn: () => fetchKeywordHistory(keyword),
    enabled: isOpen,
  });

  if (!isOpen) return null;

  const chartData = data?.history
    .map((h) => ({
      date: h.analysis_runs.run_date.slice(0, 10),
      rank: h.rank,
    }))
    .reverse();

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-[#1e293b] border border-[#334155] rounded-xl w-full max-w-lg mx-4 p-6 relative"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <h2 className="text-lg font-bold text-white mb-1">
          &quot;{keyword}&quot; 키워드 히스토리
        </h2>
        <p className="text-slate-400 text-sm mb-4">순위 변동 추이 (낮을수록 상위)</p>

        {isLoading && (
          <div className="h-[250px] bg-[#334155]/50 rounded-lg animate-pulse" />
        )}

        {error && (
          <div className="bg-red-900/30 border border-red-700 text-red-300 px-4 py-3 rounded-lg text-sm">
            {error instanceof Error ? error.message : "데이터를 불러오지 못했습니다."}
          </div>
        )}

        {data && chartData && (
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="date"
                stroke="#94a3b8"
                tick={{ fill: "#94a3b8", fontSize: 12 }}
              />
              <YAxis
                reversed
                stroke="#94a3b8"
                tick={{ fill: "#94a3b8", fontSize: 12 }}
                allowDecimals={false}
                label={{
                  value: "순위",
                  angle: -90,
                  position: "insideLeft",
                  fill: "#94a3b8",
                  fontSize: 12,
                }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  color: "#f1f5f9",
                }}
              />
              <Line
                type="monotone"
                dataKey="rank"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: "#3b82f6", r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
