"use client";

interface RegionToggleProps {
  value: string;
  onChange: (value: string) => void;
}

const REGIONS = [
  { label: "한국", value: "kr" },
  { label: "글로벌", value: "global" },
  { label: "통합", value: "all" },
];

export default function RegionToggle({ value, onChange }: RegionToggleProps) {
  return (
    <div className="flex bg-[#1e293b] rounded-lg border border-slate-700 overflow-hidden">
      {REGIONS.map((region) => (
        <button
          key={region.value}
          onClick={() => onChange(region.value)}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            value === region.value
              ? "bg-blue-600 text-white"
              : "text-slate-400 hover:text-white hover:bg-slate-700"
          }`}
        >
          {region.label}
        </button>
      ))}
    </div>
  );
}
