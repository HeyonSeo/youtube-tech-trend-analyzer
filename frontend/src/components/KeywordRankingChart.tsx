"use client";

import { KeywordItem } from "@/lib/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface KeywordRankingChartProps {
  keywords: KeywordItem[];
  height?: number;
}

const CATEGORY_COLORS: Record<string, string> = {
  AI: "#3b82f6",
  Web: "#10b981",
  Mobile: "#f59e0b",
  DevOps: "#8b5cf6",
  Database: "#ef4444",
  Cloud: "#06b6d4",
  Security: "#f97316",
  Language: "#ec4899",
  Framework: "#14b8a6",
  Other: "#6b7280",
};

function getCategoryColor(category: string): string {
  return CATEGORY_COLORS[category] || CATEGORY_COLORS.Other;
}

export default function KeywordRankingChart({
  keywords,
  height = 400,
}: KeywordRankingChartProps) {
  const chartData = [...keywords].reverse();

  return (
    <div className="bg-[#1e293b] rounded-xl p-5 border border-slate-700">
      <h3 className="text-lg font-semibold text-white mb-4">
        키워드 TOP {keywords.length}
      </h3>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis type="number" stroke="#94a3b8" fontSize={12} />
          <YAxis
            type="category"
            dataKey="keyword"
            stroke="#94a3b8"
            fontSize={12}
            width={100}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1e293b",
              border: "1px solid #475569",
              borderRadius: "8px",
              color: "#f1f5f9",
            }}
            formatter={(value, _name, props) => [
              `${value}회`,
              (props?.payload as KeywordItem)?.category ?? "",
            ]}
          />
          <Bar dataKey="count" radius={[0, 6, 6, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={index} fill={getCategoryColor(entry.category)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
