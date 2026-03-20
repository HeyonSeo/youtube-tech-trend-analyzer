"use client";

import { useState } from "react";
import { fetchAnalysis, AnalysisResult } from "@/lib/api";
import KeywordRankingChart from "@/components/KeywordRankingChart";
import RegionToggle from "@/components/RegionToggle";
import { Loader2, Play } from "lucide-react";

export default function KeywordsPage() {
  const [region, setRegion] = useState("all");
  const [periodDays, setPeriodDays] = useState(7);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchAnalysis(periodDays, region, 30);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "분석 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">키워드 분석</h1>
        <p className="text-slate-400 text-sm mt-1">
          테크 트렌드 키워드를 상세 분석합니다
        </p>
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
          onClick={handleAnalyze}
          disabled={loading}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-5 py-2 rounded-lg font-medium transition-colors text-sm"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          분석 시작
        </button>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 text-red-300 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <Loader2 className="w-10 h-10 animate-spin text-blue-400" />
          <p className="text-slate-400">키워드를 분석하고 있습니다...</p>
        </div>
      )}

      {data && !loading && (
        <div className="space-y-6">
          <KeywordRankingChart keywords={data.keywords} height={600} />

          <div className="bg-[#1e293b] rounded-xl border border-slate-700 overflow-hidden">
            <div className="p-5 border-b border-slate-700">
              <h3 className="text-lg font-semibold text-white">키워드 목록</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-slate-700 bg-slate-800/50">
                    <th className="px-4 py-3 text-sm font-medium text-slate-400 w-20">
                      순위
                    </th>
                    <th className="px-4 py-3 text-sm font-medium text-slate-400">
                      키워드
                    </th>
                    <th className="px-4 py-3 text-sm font-medium text-slate-400 w-28 text-right">
                      빈도
                    </th>
                    <th className="px-4 py-3 text-sm font-medium text-slate-400 w-32">
                      카테고리
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.keywords.map((kw) => (
                    <tr
                      key={kw.rank}
                      className="border-b border-slate-700/50 hover:bg-slate-800/30 transition-colors"
                    >
                      <td className="px-4 py-3 text-center text-slate-300 font-medium">
                        {kw.rank}
                      </td>
                      <td className="px-4 py-3 text-white font-medium">
                        {kw.keyword}
                      </td>
                      <td className="px-4 py-3 text-slate-300 text-right tabular-nums">
                        {kw.count.toLocaleString("ko-KR")}
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-block px-2.5 py-1 text-xs font-medium rounded-full bg-blue-600/20 text-blue-300 border border-blue-500/30">
                          {kw.category}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {data.keywords.length === 0 && (
                <div className="text-center py-12 text-slate-500">
                  데이터가 없습니다.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {!data && !loading && !error && (
        <div className="flex flex-col items-center justify-center py-24 gap-4 text-slate-500">
          <Play className="w-16 h-16" />
          <p className="text-lg">위의 &quot;분석 시작&quot; 버튼을 클릭하여 키워드를 분석하세요</p>
        </div>
      )}
    </div>
  );
}
