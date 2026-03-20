"use client";

import { VideoItem } from "@/lib/api";

interface VideoTableProps {
  videos: VideoItem[];
  showLink?: boolean;
}

function formatNumber(n: number): string {
  return n.toLocaleString("ko-KR");
}

export default function VideoTable({ videos, showLink = false }: VideoTableProps) {
  return (
    <div className="bg-white dark:bg-[#1e293b] rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden">
      <div className="p-5 border-b border-gray-200 dark:border-slate-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">인기 영상</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left" aria-label="조회수 상위 영상 목록">
          <thead>
            <tr className="border-b border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-800/50">
              <th className="px-4 py-3 text-sm font-medium text-slate-400 w-16">
                순위
              </th>
              <th className="px-4 py-3 text-sm font-medium text-slate-400 w-32">
                썸네일
              </th>
              <th className="px-4 py-3 text-sm font-medium text-slate-400">
                제목
              </th>
              <th className="px-4 py-3 text-sm font-medium text-slate-400 w-36">
                채널
              </th>
              <th className="px-4 py-3 text-sm font-medium text-slate-400 w-28 text-right">
                조회수
              </th>
              <th className="px-4 py-3 text-sm font-medium text-slate-400 w-24 text-right">
                좋아요
              </th>
            </tr>
          </thead>
          <tbody>
            {videos.map((video, idx) => (
              <tr
                key={video.video_id}
                className="border-b border-gray-200 dark:border-slate-700/50 hover:bg-gray-50 dark:hover:bg-slate-800/30 transition-colors"
              >
                <td className="px-4 py-3 text-center text-gray-600 dark:text-slate-300 font-medium">
                  {idx + 1}
                </td>
                <td className="px-4 py-3">
                  <img
                    src={video.thumbnail_url}
                    alt={video.title}
                    width={120}
                    height={68}
                    className="rounded-md object-cover"
                    loading="lazy"
                  />
                </td>
                <td className="px-4 py-3">
                  {showLink ? (
                    <a
                      href={`https://www.youtube.com/watch?v=${video.video_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 hover:underline line-clamp-2"
                    >
                      {video.title}
                    </a>
                  ) : (
                    <span className="text-gray-900 dark:text-white line-clamp-2">{video.title}</span>
                  )}
                </td>
                <td className="px-4 py-3 text-gray-600 dark:text-slate-300 truncate max-w-[140px]">
                  {video.channel}
                </td>
                <td className="px-4 py-3 text-gray-600 dark:text-slate-300 text-right tabular-nums">
                  {formatNumber(video.views)}
                </td>
                <td className="px-4 py-3 text-gray-600 dark:text-slate-300 text-right tabular-nums">
                  {formatNumber(video.likes)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {videos.length === 0 && (
          <div className="text-center py-12 text-slate-500">
            데이터가 없습니다.
          </div>
        )}
      </div>
    </div>
  );
}
