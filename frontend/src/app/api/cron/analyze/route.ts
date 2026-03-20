import { NextRequest, NextResponse } from "next/server";

/**
 * Vercel Cron Job — Daily analysis trigger
 *
 * Runs at 06:00 KST (21:00 UTC) via vercel.json cron configuration.
 * Calls the backend /api/analyze endpoint to refresh cached analysis data.
 */

export const runtime = "edge";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  // Verify the request is from Vercel Cron (production) or has the right secret
  const authHeader = request.headers.get("authorization");
  const cronSecret = process.env.CRON_SECRET;

  if (cronSecret && authHeader !== `Bearer ${cronSecret}`) {
    return NextResponse.json(
      { error: "Unauthorized" },
      { status: 401 }
    );
  }

  const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL;

  if (!backendUrl) {
    return NextResponse.json(
      { error: "BACKEND_URL is not configured" },
      { status: 500 }
    );
  }

  try {
    // Trigger analysis for all regions
    const regions = ["kr", "global"] as const;
    const results = await Promise.allSettled(
      regions.map(async (region) => {
        const url = `${backendUrl}/api/analyze?period_days=7&region=${region}&top_n=10`;
        const res = await fetch(url, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
          signal: AbortSignal.timeout(120_000), // 2-minute timeout per request
        });

        if (!res.ok) {
          const body = await res.text();
          throw new Error(`Backend returned ${res.status}: ${body}`);
        }

        return { region, status: res.status };
      })
    );

    const summary = results.map((r, i) => ({
      region: regions[i],
      success: r.status === "fulfilled",
      detail: r.status === "fulfilled" ? r.value : (r.reason as Error).message,
    }));

    const allOk = summary.every((s) => s.success);

    return NextResponse.json(
      {
        message: allOk
          ? "Daily analysis completed successfully"
          : "Daily analysis completed with errors",
        timestamp: new Date().toISOString(),
        results: summary,
      },
      { status: allOk ? 200 : 207 }
    );
  } catch (error) {
    console.error("[Cron] Daily analysis failed:", error);
    return NextResponse.json(
      {
        error: "Daily analysis failed",
        detail: error instanceof Error ? error.message : String(error),
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}
