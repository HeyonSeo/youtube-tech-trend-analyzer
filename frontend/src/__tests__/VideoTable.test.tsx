import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import VideoTable from "@/components/VideoTable";
import type { VideoItem } from "@/lib/api";

const mockVideos: VideoItem[] = [
  {
    video_id: "abc123",
    title: "iPhone 16 리뷰",
    channel: "테크채널",
    views: 1500000,
    likes: 45000,
    published_at: "2026-03-15",
    language: "ko",
    thumbnail_url: "https://img.youtube.com/vi/abc123/default.jpg",
  },
  {
    video_id: "def456",
    title: "Galaxy S26 언박싱",
    channel: "리뷰어",
    views: 800000,
    likes: 20000,
    published_at: "2026-03-14",
    language: "ko",
    thumbnail_url: "https://img.youtube.com/vi/def456/default.jpg",
  },
];

describe("VideoTable", () => {
  it("renders table with correct headers", () => {
    render(<VideoTable videos={mockVideos} />);
    expect(screen.getByText("순위")).toBeInTheDocument();
    expect(screen.getByText("제목")).toBeInTheDocument();
    expect(screen.getByText("채널")).toBeInTheDocument();
    expect(screen.getByText("조회수")).toBeInTheDocument();
  });

  it("renders video titles", () => {
    render(<VideoTable videos={mockVideos} />);
    expect(screen.getByText("iPhone 16 리뷰")).toBeInTheDocument();
    expect(screen.getByText("Galaxy S26 언박싱")).toBeInTheDocument();
  });

  it("shows empty message when no videos", () => {
    render(<VideoTable videos={[]} />);
    expect(screen.getByText("데이터가 없습니다.")).toBeInTheDocument();
  });

  it("renders links when showLink is true", () => {
    render(<VideoTable videos={mockVideos} showLink={true} />);
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute("href", "https://www.youtube.com/watch?v=abc123");
  });

  it("has accessible table label", () => {
    render(<VideoTable videos={mockVideos} />);
    expect(screen.getByLabelText("조회수 상위 영상 목록")).toBeInTheDocument();
  });
});
