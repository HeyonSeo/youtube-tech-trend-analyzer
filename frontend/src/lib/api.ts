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
