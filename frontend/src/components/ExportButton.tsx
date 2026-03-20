"use client";

import { useState, useRef, useEffect } from "react";
import { Download, ChevronDown } from "lucide-react";
import { getExportUrl } from "@/lib/api";

interface ExportButtonProps {
  periodDays: number;
  region: string;
}

export default function ExportButton({ periodDays, region }: ExportButtonProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleExport(format: "csv" | "xlsx") {
    const url = getExportUrl(format, periodDays, region);
    window.open(url, "_blank");
    setOpen(false);
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 bg-[#1e293b] hover:bg-slate-700 text-white px-4 py-2 rounded-lg border border-slate-600 transition-colors text-sm"
      >
        <Download className="w-4 h-4" />
        내보내기
        <ChevronDown className={`w-4 h-4 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-44 bg-[#1e293b] border border-slate-600 rounded-lg shadow-xl z-50 overflow-hidden">
          <button
            onClick={() => handleExport("csv")}
            className="w-full text-left px-4 py-3 text-sm text-white hover:bg-slate-700 transition-colors"
          >
            CSV 다운로드
          </button>
          <button
            onClick={() => handleExport("xlsx")}
            className="w-full text-left px-4 py-3 text-sm text-white hover:bg-slate-700 transition-colors border-t border-slate-700"
          >
            Excel 다운로드
          </button>
        </div>
      )}
    </div>
  );
}
