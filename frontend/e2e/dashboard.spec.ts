import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test("loads and shows main heading", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=TechPulse")).toBeVisible();
  });

  test("has navigation links", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=대시보드")).toBeVisible();
    await expect(page.locator("text=트렌드")).toBeVisible();
    await expect(page.locator("text=설정")).toBeVisible();
  });

  test("has analyze button", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=분석 시작")).toBeVisible();
  });
});
