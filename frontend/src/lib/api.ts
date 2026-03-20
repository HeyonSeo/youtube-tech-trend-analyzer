const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface VideoItem {
  video_id: string;
  title: string;
  channel: string;
  views: number;
  likes: number;
  published_at: string;
  language: string;
  thumbnail_url: string;
}

export interface KeywordItem {
  rank: number;
  keyword: string;
  count: number;
  category: string;
}

export interface InterestItem {
  rank: number;
  category: string;
  score: number;
  ratio: number;
}

export interface AnalysisMetadata {
  video_count: number;
  period_days: number;
  region: string;
  run_date: string;
  queries_used: string[];
}

export interface AnalysisResult {
  metadata: AnalysisMetadata;
  videos: VideoItem[];
  keywords: KeywordItem[];
  interests: InterestItem[];
}

export async function fetchAnalysis(periodDays = 7, region = "all", topN = 10): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/api/analyze?period_days=${periodDays}&region=${region}&top_n=${topN}`);
  if (!res.ok) throw new Error("Analysis failed");
  return res.json();
}

export function getExportUrl(format: "csv" | "xlsx", periodDays = 7, region = "all"): string {
  return `${API_BASE}/api/export/${format}?period_days=${periodDays}&region=${region}`;
}

export interface TrendItem {
  keyword: string;
  rank: number;
  count: number;
  category: string;
  rank_change: number | null;
  is_new: boolean;
  previous_rank: number | null;
}

export interface TrendComparison {
  current_date: string;
  previous_date: string;
  trends: TrendItem[];
}

export interface KeywordHistory {
  keyword: string;
  history: Array<{
    count: number;
    rank: number;
    run_id: string;
    analysis_runs: { run_date: string };
  }>;
}

export async function fetchTrends(region = "all", weeks = 2): Promise<TrendComparison> {
  const res = await fetch(`${API_BASE}/api/trends?region=${region}&weeks=${weeks}`);
  if (!res.ok) throw new Error("Trend fetch failed");
  return res.json();
}

export async function fetchKeywordHistory(keyword: string, limit = 12): Promise<KeywordHistory> {
  const res = await fetch(`${API_BASE}/api/trends/${encodeURIComponent(keyword)}?limit=${limit}`);
  if (!res.ok) throw new Error("History fetch failed");
  return res.json();
}

export interface AppSettings {
  search_queries: {
    kr: string[];
    en: string[];
  };
  categories: string[];
  cache_ttl_seconds: number;
}

export async function fetchSettings(): Promise<AppSettings> {
  const res = await fetch(`${API_BASE}/api/settings`);
  if (!res.ok) throw new Error("Settings fetch failed");
  return res.json();
}

export async function clearCache(): Promise<void> {
  const res = await fetch(`${API_BASE}/api/cache/clear`, { method: "POST" });
  if (!res.ok) throw new Error("Cache clear failed");
}
