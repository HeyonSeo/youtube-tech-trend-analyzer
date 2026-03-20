"use client";

import { AnalysisResult } from "@/lib/api";
import { BarChart3, Hash, Star, Globe } from "lucide-react";

interface SummaryCardsProps {
  data: AnalysisResult;
}

export default function SummaryCards({ data }: SummaryCardsProps) {
  const topKeyword = data.keywords.length > 0 ? data.keywords[0].keyword : "-";
  const topInterest = data.interests.length > 0 ? data.interests[0].category : "-";
  const regionLabel =
    data.metadata.region === "kr"
      ? "한국"
      : data.metadata.region === "global"
      ? "글로벌"
      : "통합";

  const cards = [
    {
      label: "수집 영상 수",
      value: data.metadata.video_count.toLocaleString(),
      icon: <BarChart3 className="w-6 h-6 text-blue-400" />,
    },
    {
      label: "TOP 키워드",
      value: topKeyword,
      icon: <Hash className="w-6 h-6 text-green-400" />,
    },
    {
      label: "1위 관심사",
      value: topInterest,
      icon: <Star className="w-6 h-6 text-yellow-400" />,
    },
    {
      label: "분석 지역",
      value: regionLabel,
      icon: <Globe className="w-6 h-6 text-purple-400" />,
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-[#1e293b] rounded-xl p-5 flex items-center gap-4 border border-slate-700"
        >
          <div className="flex-shrink-0 bg-slate-800 rounded-lg p-3">
            {card.icon}
          </div>
          <div>
            <p className="text-sm text-slate-400">{card.label}</p>
            <p className="text-xl font-bold text-white truncate max-w-[140px]">
              {card.value}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
