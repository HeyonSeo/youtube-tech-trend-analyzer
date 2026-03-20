import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import SummaryCards from "@/components/SummaryCards";
import type { AnalysisResult } from "@/lib/api";

const mockData: AnalysisResult = {
  metadata: {
    video_count: 150,
    period_days: 7,
    region: "kr",
    run_date: "2026-03-20",
    queries_used: ["test"],
  },
  videos: [],
  keywords: [
    { rank: 1, keyword: "React", count: 42, category: "Frontend" },
    { rank: 2, keyword: "AI", count: 30, category: "ML" },
  ],
  interests: [
    { rank: 1, category: "웹 개발", score: 85, ratio: 0.4 },
  ],
};

describe("SummaryCards", () => {
  it("renders 4 summary cards", () => {
    render(<SummaryCards data={mockData} />);
    expect(screen.getByLabelText("수집 영상 수")).toBeInTheDocument();
    expect(screen.getByLabelText("TOP 키워드")).toBeInTheDocument();
    expect(screen.getByLabelText("1위 관심사")).toBeInTheDocument();
    expect(screen.getByLabelText("분석 지역")).toBeInTheDocument();
  });

  it("displays video count formatted with locale", () => {
    render(<SummaryCards data={mockData} />);
    expect(screen.getByText("150")).toBeInTheDocument();
  });

  it("displays the top keyword", () => {
    render(<SummaryCards data={mockData} />);
    expect(screen.getByText("React")).toBeInTheDocument();
  });

  it("displays the top interest category", () => {
    render(<SummaryCards data={mockData} />);
    expect(screen.getByText("웹 개발")).toBeInTheDocument();
  });

  it("displays region label as 한국 for kr", () => {
    render(<SummaryCards data={mockData} />);
    expect(screen.getByText("한국")).toBeInTheDocument();
  });

  it("displays 글로벌 for global region", () => {
    const globalData = {
      ...mockData,
      metadata: { ...mockData.metadata, region: "global" },
    };
    render(<SummaryCards data={globalData} />);
    expect(screen.getByText("글로벌")).toBeInTheDocument();
  });

  it("displays 통합 for all region", () => {
    const allData = {
      ...mockData,
      metadata: { ...mockData.metadata, region: "all" },
    };
    render(<SummaryCards data={allData} />);
    expect(screen.getByText("통합")).toBeInTheDocument();
  });

  it("shows dash when keywords array is empty", () => {
    const emptyData = { ...mockData, keywords: [], interests: [] };
    render(<SummaryCards data={emptyData} />);
    const dashes = screen.getAllByText("-");
    expect(dashes.length).toBeGreaterThanOrEqual(2);
  });
});
