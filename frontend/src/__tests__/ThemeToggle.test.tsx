import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import ThemeToggle from "@/components/ThemeToggle";

describe("ThemeToggle", () => {
  it("renders a button with aria-label", () => {
    render(<ThemeToggle />);
    expect(screen.getByLabelText("테마 전환")).toBeInTheDocument();
  });

  it("toggles theme on click and saves to localStorage", () => {
    render(<ThemeToggle />);
    const button = screen.getByLabelText("테마 전환");
    fireEvent.click(button);
    expect(window.localStorage.setItem).toHaveBeenCalled();
  });

  it("renders an SVG icon", () => {
    render(<ThemeToggle />);
    const button = screen.getByLabelText("테마 전환");
    const svg = button.querySelector("svg");
    expect(svg).not.toBeNull();
  });
});
