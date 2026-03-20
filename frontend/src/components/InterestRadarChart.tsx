"use client";

import { InterestItem } from "@/lib/api";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface InterestRadarChartProps {
  interests: InterestItem[];
}

export default function InterestRadarChart({ interests }: InterestRadarChartProps) {
  const chartData = interests.map((item) => ({
    category: item.category,
    score: item.score,
    ratio: item.ratio,
  }));

  return (
    <div className="bg-[#1e293b] rounded-xl p-5 border border-slate-700">
      <h3 className="text-lg font-semibold text-white mb-4">
        관심사 분포
      </h3>
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart data={chartData} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke="#334155" />
          <PolarAngleAxis dataKey="category" stroke="#94a3b8" fontSize={12} />
          <PolarRadiusAxis stroke="#475569" fontSize={10} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1e293b",
              border: "1px solid #475569",
              borderRadius: "8px",
              color: "#f1f5f9",
            }}
            formatter={(value) => [`${Number(value).toFixed(1)}점`]}
          />
          <Radar
            name="관심도"
            dataKey="score"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.3}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
