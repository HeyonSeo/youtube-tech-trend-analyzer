import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import ExportButton from "@/components/ExportButton";

// Mock window.open
vi.stubGlobal("open", vi.fn());

describe("ExportButton", () => {
  it("renders export button with label", () => {
    render(<ExportButton periodDays={7} region="kr" />);
    expect(screen.getByLabelText("내보내기 메뉴")).toBeInTheDocument();
    expect(screen.getByText("내보내기")).toBeInTheDocument();
  });

  it("opens dropdown on click", () => {
    render(<ExportButton periodDays={7} region="kr" />);
    fireEvent.click(screen.getByLabelText("내보내기 메뉴"));
    expect(screen.getByText("CSV 다운로드")).toBeInTheDocument();
    expect(screen.getByText("Excel 다운로드")).toBeInTheDocument();
  });

  it("calls window.open on CSV click", () => {
    render(<ExportButton periodDays={7} region="kr" />);
    fireEvent.click(screen.getByLabelText("내보내기 메뉴"));
    fireEvent.click(screen.getByText("CSV 다운로드"));
    expect(window.open).toHaveBeenCalled();
  });

  it("closes dropdown after export selection", () => {
    render(<ExportButton periodDays={7} region="kr" />);
    fireEvent.click(screen.getByLabelText("내보내기 메뉴"));
    fireEvent.click(screen.getByText("Excel 다운로드"));
    expect(screen.queryByText("CSV 다운로드")).not.toBeInTheDocument();
  });
});
