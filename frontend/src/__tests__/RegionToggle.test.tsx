import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import RegionToggle from "@/components/RegionToggle";

describe("RegionToggle", () => {
  it("renders three region buttons", () => {
    render(<RegionToggle value="kr" onChange={vi.fn()} />);
    expect(screen.getByText("한국")).toBeInTheDocument();
    expect(screen.getByText("글로벌")).toBeInTheDocument();
    expect(screen.getByText("통합")).toBeInTheDocument();
  });

  it("calls onChange with correct value when clicked", () => {
    const onChange = vi.fn();
    render(<RegionToggle value="kr" onChange={onChange} />);
    fireEvent.click(screen.getByText("글로벌"));
    expect(onChange).toHaveBeenCalledWith("global");
  });

  it("has aria-labels on buttons", () => {
    render(<RegionToggle value="kr" onChange={vi.fn()} />);
    expect(screen.getByLabelText("한국 지역 필터")).toBeInTheDocument();
    expect(screen.getByLabelText("글로벌 지역 필터")).toBeInTheDocument();
    expect(screen.getByLabelText("통합 지역 필터")).toBeInTheDocument();
  });

  it("highlights active region", () => {
    render(<RegionToggle value="global" onChange={vi.fn()} />);
    const globalBtn = screen.getByText("글로벌");
    expect(globalBtn.className).toContain("bg-blue-600");
  });
});
