"""Email report generation and sending."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app import config

logger = logging.getLogger(__name__)


def generate_report_html(keywords: list, interests: dict, top_video: dict | None, trends: list | None = None) -> str:
    """Generate HTML email report."""

    # Build keyword rows
    kw_rows = ""
    for kw in keywords[:10]:
        trend_icon = ""
        if trends:
            match = next((t for t in trends if t.get("keyword") == kw.get("keyword", kw.keyword if hasattr(kw, 'keyword') else "")), None)
            if match:
                rc = match.get("rank_change")
                if match.get("is_new"):
                    trend_icon = "\U0001f195"
                elif rc and rc > 0:
                    trend_icon = f"\u25b2{rc}"
                elif rc and rc < 0:
                    trend_icon = f"\u25bc{abs(rc)}"

        keyword = kw.keyword if hasattr(kw, 'keyword') else kw.get("keyword", "")
        count = kw.count if hasattr(kw, 'count') else kw.get("count", 0)
        rank = kw.rank if hasattr(kw, 'rank') else kw.get("rank", 0)
        category = kw.category if hasattr(kw, 'category') else kw.get("category", "")

        kw_rows += f"""<tr>
            <td style="padding:8px 12px;border-bottom:1px solid #334155;color:#94a3b8;">{rank}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #334155;font-weight:600;color:#e2e8f0;">{keyword}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #334155;color:#94a3b8;text-align:right;">{count}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #334155;color:#94a3b8;">{category}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #334155;color:#22c55e;">{trend_icon}</td>
        </tr>"""

    # Top video section
    video_section = ""
    if top_video:
        title = top_video.title if hasattr(top_video, 'title') else top_video.get("title", "")
        channel = top_video.channel if hasattr(top_video, 'channel') else top_video.get("channel", "")
        views = top_video.views if hasattr(top_video, 'views') else top_video.get("views", 0)
        video_section = f"""
        <div style="background:#1e293b;border-radius:12px;padding:20px;margin-top:24px;">
            <h3 style="color:#94a3b8;font-size:14px;margin:0 0 8px;">\U0001f3c6 \uc870\ud68c\uc218 1\uc704 \uc601\uc0c1</h3>
            <p style="color:#e2e8f0;font-size:16px;font-weight:600;margin:0 0 4px;">{title}</p>
            <p style="color:#94a3b8;font-size:13px;margin:0;">{channel} \u00b7 \uc870\ud68c\uc218 {views:,}</p>
        </div>"""

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:600px;margin:0 auto;padding:32px 20px;">
    <div style="text-align:center;margin-bottom:32px;">
        <h1 style="color:#3b82f6;font-size:24px;margin:0;">\U0001f4ca TechPulse \uc8fc\uac04 \ub9ac\ud3ec\ud2b8</h1>
        <p style="color:#94a3b8;font-size:14px;margin:8px 0 0;">{now} \uae30\uc900</p>
    </div>

    <div style="background:#1e293b;border-radius:12px;padding:20px;margin-bottom:24px;">
        <h2 style="color:#e2e8f0;font-size:18px;margin:0 0 16px;">\ud0a4\uc6cc\ub4dc TOP 10</h2>
        <table style="width:100%;border-collapse:collapse;">
            <thead>
                <tr style="border-bottom:2px solid #334155;">
                    <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:12px;">\uc21c\uc704</th>
                    <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:12px;">\ud0a4\uc6cc\ub4dc</th>
                    <th style="padding:8px 12px;text-align:right;color:#64748b;font-size:12px;">\ube48\ub3c4</th>
                    <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:12px;">\uce74\ud14c\uace0\ub9ac</th>
                    <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:12px;">\ubcc0\ub3d9</th>
                </tr>
            </thead>
            <tbody>{kw_rows}</tbody>
        </table>
    </div>

    {video_section}

    <div style="text-align:center;margin-top:32px;">
        <p style="color:#64748b;font-size:12px;">TechPulse \u2014 YouTube \ud14c\ud06c \ub9ac\ubdf0 \ud2b8\ub80c\ub4dc \ubd84\uc11d\uae30</p>
    </div>
</div>
</body></html>"""


def send_report(recipients: list[str], html_content: str, subject: str | None = None) -> bool:
    """Send email report via Resend."""
    if not config.EMAIL_ENABLED:
        logger.warning("Email not configured (RESEND_API_KEY missing)")
        return False

    import resend
    resend.api_key = config.RESEND_API_KEY

    if not subject:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        subject = f"[TechPulse] \uc8fc\uac04 \ud14c\ud06c \ud2b8\ub80c\ub4dc \ub9ac\ud3ec\ud2b8 \u2014 {now}"

    try:
        resend.Emails.send({
            "from": config.REPORT_FROM_EMAIL,
            "to": recipients,
            "subject": subject,
            "html": html_content,
        })
        logger.info(f"Report sent to {len(recipients)} recipients")
        return True
    except Exception as e:
        logger.error(f"Failed to send report: {e}")
        return False
