#!/usr/bin/env python3
"""
MedContext Analytics Report
============================
Fetches analytics data from the API and generates an HTML report with charts.

Usage:
    python scripts/analytics_report.py
    python scripts/analytics_report.py --all-time
    python scripts/analytics_report.py --days 7
    python scripts/analytics_report.py --url https://medcontext.drjforrest.com --output report.html
    python scripts/analytics_report.py --no-open   # save without opening browser
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.gridspec import GridSpec
except ImportError:
    print("Error: matplotlib is required. Install with: pip install matplotlib", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
PALETTE = {
    "primary": "#6366f1",     # indigo
    "success": "#22c55e",     # green
    "error": "#ef4444",       # red
    "warning": "#f59e0b",     # amber
    "muted": "#94a3b8",       # slate-400
    "misinformation": "#ef4444",
    "legitimate": "#22c55e",
    "unknown": "#94a3b8",
}
BG = "#0f1117"
CARD = "#1a1d2e"
TEXT = "#e2e8f0"
GRID = "#2d3748"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": CARD,
    "axes.edgecolor": GRID,
    "axes.labelcolor": TEXT,
    "xtick.color": TEXT,
    "ytick.color": TEXT,
    "text.color": TEXT,
    "grid.color": GRID,
    "grid.alpha": 0.5,
    "font.family": "DejaVu Sans",
    "font.size": 10,
})


# ---------------------------------------------------------------------------
# API fetch
# ---------------------------------------------------------------------------

def fetch_stats(base_url: str, *, days: int = 30, all_time: bool = False) -> dict:
    params = "all_time=true" if all_time else f"days={days}"
    url = f"{base_url.rstrip('/')}/api/v1/analytics/stats?{params}"
    try:
        with urlopen(url, timeout=15) as resp:
            return json.loads(resp.read())
    except URLError as exc:
        print(f"Error fetching {url}: {exc}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------

def _fig_to_b64(fig: plt.Figure) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def chart_runs_per_day(runs_per_day: list[dict]) -> str:
    dates = [r["date"][5:] for r in runs_per_day]  # MM-DD
    counts = [r["count"] for r in runs_per_day]

    fig, ax = plt.subplots(figsize=(8, 3.2), facecolor=BG)
    bars = ax.bar(dates, counts, color=PALETTE["primary"], alpha=0.85, zorder=3)
    ax.set_title("Runs per Day (last 7 days)", color=TEXT, pad=10, fontsize=11)
    ax.set_ylabel("Runs", color=TEXT)
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.grid(axis="y", zorder=0)
    ax.set_axisbelow(True)

    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.05,
                str(count),
                ha="center", va="bottom", fontsize=9, color=TEXT,
            )

    plt.tight_layout()
    result = _fig_to_b64(fig)
    plt.close(fig)
    return result


def chart_verdict_distribution(verdict_counts: dict) -> str | None:
    if not verdict_counts:
        return None

    labels = list(verdict_counts.keys())
    values = list(verdict_counts.values())
    colours = [PALETTE.get(lbl, PALETTE["muted"]) for lbl in labels]

    fig, ax = plt.subplots(figsize=(4, 3.5), facecolor=BG)
    wedges, texts, autotexts = ax.pie(
        values,
        labels=None,
        colors=colours,
        autopct="%1.0f%%",
        startangle=140,
        wedgeprops={"linewidth": 1.5, "edgecolor": BG},
    )
    for at in autotexts:
        at.set_color(TEXT)
        at.set_fontsize(10)

    ax.legend(
        wedges, [f"{lbl} ({v})" for lbl, v in zip(labels, values)],
        loc="lower center", bbox_to_anchor=(0.5, -0.18),
        fontsize=9, frameon=False, labelcolor=TEXT,
        ncol=min(len(labels), 2),
    )
    ax.set_title("Verdict Distribution", color=TEXT, pad=8, fontsize=11)
    plt.tight_layout()
    result = _fig_to_b64(fig)
    plt.close(fig)
    return result


def chart_ip_distribution(ip_counts: dict, max_show: int = 15) -> str | None:
    if not ip_counts:
        return None

    items = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:max_show]
    ips = [item[0] for item in items]
    counts = [item[1] for item in items]

    fig_h = max(3.0, len(ips) * 0.45)
    fig, ax = plt.subplots(figsize=(7, fig_h), facecolor=BG)
    bars = ax.barh(ips[::-1], counts[::-1], color=PALETTE["primary"], alpha=0.8, zorder=3)
    ax.set_title("Top IPs by Run Count", color=TEXT, pad=10, fontsize=11)
    ax.set_xlabel("Runs", color=TEXT)
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.grid(axis="x", zorder=0)
    ax.set_axisbelow(True)

    for bar, count in zip(bars, counts[::-1]):
        ax.text(
            bar.get_width() + 0.05,
            bar.get_y() + bar.get_height() / 2,
            str(count),
            va="center", fontsize=9, color=TEXT,
        )

    plt.tight_layout()
    result = _fig_to_b64(fig)
    plt.close(fig)
    return result


def chart_source_distribution(source_counts: dict) -> str | None:
    if not source_counts or len(source_counts) < 2:
        return None  # not interesting if only one source

    labels = list(source_counts.keys())
    values = list(source_counts.values())
    colours = [PALETTE["primary"], PALETTE["success"], PALETTE["warning"], PALETTE["muted"]][:len(labels)]

    fig, ax = plt.subplots(figsize=(4, 3.5), facecolor=BG)
    wedges, texts, autotexts = ax.pie(
        values,
        labels=None,
        colors=colours,
        autopct="%1.0f%%",
        startangle=90,
        wedgeprops={"linewidth": 1.5, "edgecolor": BG},
    )
    for at in autotexts:
        at.set_color(TEXT)
        at.set_fontsize(10)

    ax.legend(
        wedges, [f"{lbl} ({v})" for lbl, v in zip(labels, values)],
        loc="lower center", bbox_to_anchor=(0.5, -0.18),
        fontsize=9, frameon=False, labelcolor=TEXT,
        ncol=min(len(labels), 2),
    )
    ax.set_title("Source Distribution", color=TEXT, pad=8, fontsize=11)
    plt.tight_layout()
    result = _fig_to_b64(fig)
    plt.close(fig)
    return result


# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>MedContext Analytics Report</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0f1117;
      color: #e2e8f0;
      padding: 2rem;
      line-height: 1.6;
    }}
    h1 {{ font-size: 1.6rem; font-weight: 700; color: #f1f5f9; margin-bottom: 0.25rem; }}
    h2 {{ font-size: 1.1rem; font-weight: 600; color: #cbd5e1; margin-bottom: 1rem; border-bottom: 1px solid #2d3748; padding-bottom: 0.4rem; }}
    .subtitle {{ color: #64748b; font-size: 0.9rem; margin-bottom: 2rem; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 1rem;
      margin-bottom: 2.5rem;
    }}
    .metric {{
      background: #1a1d2e;
      border: 1px solid #2d3748;
      border-radius: 10px;
      padding: 1rem 1.2rem;
    }}
    .metric-label {{ font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: #64748b; margin-bottom: 0.3rem; }}
    .metric-value {{ font-size: 1.6rem; font-weight: 700; color: #f1f5f9; }}
    .metric-value.success {{ color: #22c55e; }}
    .metric-value.error {{ color: #ef4444; }}
    .metric-value.info {{ color: #6366f1; }}
    .section {{ margin-bottom: 2.5rem; }}
    .charts-row {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 1.5rem;
    }}
    .chart-card {{
      background: #1a1d2e;
      border: 1px solid #2d3748;
      border-radius: 10px;
      padding: 1.2rem;
      overflow: hidden;
    }}
    .chart-card img {{ width: 100%; height: auto; display: block; }}
    .chart-card.wide {{ grid-column: 1 / -1; }}
    .ip-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
    }}
    .ip-table th, .ip-table td {{
      padding: 0.5rem 0.8rem;
      text-align: left;
      border-bottom: 1px solid #2d3748;
    }}
    .ip-table th {{ color: #64748b; font-weight: 600; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.06em; }}
    .ip-table tr:last-child td {{ border-bottom: none; }}
    .ip-table .rank {{ color: #64748b; }}
    .ip-table .count {{ font-variant-numeric: tabular-nums; }}
    .badge {{
      display: inline-block;
      padding: 0.15rem 0.5rem;
      border-radius: 999px;
      font-size: 0.72rem;
      font-weight: 600;
    }}
    .badge-green {{ background: #14532d; color: #4ade80; }}
    .badge-red {{ background: #450a0a; color: #f87171; }}
    .badge-gray {{ background: #1e293b; color: #94a3b8; }}
    footer {{
      margin-top: 3rem;
      color: #334155;
      font-size: 0.75rem;
      text-align: center;
    }}
  </style>
</head>
<body>
  <h1>MedContext Analytics Report</h1>
  <p class="subtitle">{subtitle}</p>

  <section class="section">
    <h2>Key Metrics</h2>
    <div class="metrics">
      <div class="metric">
        <div class="metric-label">Total Runs</div>
        <div class="metric-value info">{total_runs}</div>
      </div>
      <div class="metric">
        <div class="metric-label">Successful</div>
        <div class="metric-value success">{success_count}</div>
      </div>
      <div class="metric">
        <div class="metric-label">Errors</div>
        <div class="metric-value error">{error_count}</div>
      </div>
      <div class="metric">
        <div class="metric-label">Success Rate</div>
        <div class="metric-value {success_rate_class}">{success_rate}</div>
      </div>
      <div class="metric">
        <div class="metric-label">Avg Duration</div>
        <div class="metric-value">{avg_duration}</div>
      </div>
      <div class="metric">
        <div class="metric-label">Tracking Since</div>
        <div class="metric-value" style="font-size:1rem;">{tracking_start}</div>
      </div>
    </div>
  </section>

  <section class="section">
    <h2>Activity</h2>
    <div class="charts-row">
      <div class="chart-card wide">
        <img src="data:image/png;base64,{chart_runs_per_day}" alt="Runs per Day" />
      </div>
    </div>
  </section>

  {verdict_section}

  {ip_section}

  <footer>Generated {generated_at} · MedContext Analytics</footer>
</body>
</html>
"""

VERDICT_SECTION = """
  <section class="section">
    <h2>Classifications</h2>
    <div class="charts-row">
      {verdict_chart}
      {source_chart}
    </div>
  </section>
"""

VERDICT_CHART_CARD = """
      <div class="chart-card">
        <img src="data:image/png;base64,{img}" alt="Verdict Distribution" />
      </div>
"""

SOURCE_CHART_CARD = """
      <div class="chart-card">
        <img src="data:image/png;base64,{img}" alt="Source Distribution" />
      </div>
"""

IP_SECTION = """
  <section class="section">
    <h2>Access by IP</h2>
    <div class="charts-row">
      {ip_chart}
      <div class="chart-card">
        <table class="ip-table">
          <thead>
            <tr>
              <th>#</th>
              <th>IP Address</th>
              <th>Runs</th>
              <th>Share</th>
            </tr>
          </thead>
          <tbody>
            {ip_rows}
          </tbody>
        </table>
      </div>
    </div>
  </section>
"""

IP_ROW = """
            <tr>
              <td class="rank">{rank}</td>
              <td><code>{ip}</code></td>
              <td class="count">{count}</td>
              <td><span style="color:#6366f1">{pct}%</span></td>
            </tr>
"""


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_report(stats: dict) -> str:
    total = stats["total_runs"]
    success_count = stats["success_count"]
    error_count = stats["error_count"]
    success_rate = stats.get("success_rate")
    avg_ms = stats.get("avg_duration_ms")
    all_time = stats.get("all_time", False)
    period_days = stats.get("period_days")

    # Subtitle
    if all_time:
        subtitle = f"All time · from {stats['tracking_start']}"
    else:
        subtitle = f"Last {period_days} days · since {stats['since'][:10]}"
    subtitle += f" · {total} total run{'s' if total != 1 else ''}"

    # Metrics
    success_rate_str = f"{success_rate:.1f}%" if success_rate is not None else "—"
    success_rate_class = "success" if success_rate and success_rate >= 90 else ("error" if success_rate and success_rate < 70 else "")

    if avg_ms is not None:
        if avg_ms >= 60_000:
            avg_duration = f"{avg_ms / 60_000:.1f} min"
        else:
            avg_duration = f"{avg_ms / 1_000:.1f} s"
    else:
        avg_duration = "—"

    # Charts
    runs_per_day_b64 = chart_runs_per_day(stats.get("runs_per_day", []))

    verdict_counts = stats.get("verdict_distribution", {})
    source_counts = stats.get("source_distribution", {})
    ip_counts = stats.get("ip_distribution", {})

    verdict_b64 = chart_verdict_distribution(verdict_counts)
    source_b64 = chart_source_distribution(source_counts)
    ip_b64 = chart_ip_distribution(ip_counts)

    # Verdict + source section
    if verdict_b64 or source_b64:
        verdict_chart = VERDICT_CHART_CARD.format(img=verdict_b64) if verdict_b64 else ""
        source_chart = SOURCE_CHART_CARD.format(img=source_b64) if source_b64 else ""
        verdict_section = VERDICT_SECTION.format(verdict_chart=verdict_chart, source_chart=source_chart)
    else:
        verdict_section = ""

    # IP section
    if ip_counts:
        ip_total = sum(ip_counts.values())
        ip_rows = ""
        for rank, (ip, count) in enumerate(
            sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:15], start=1
        ):
            pct = f"{count / ip_total * 100:.0f}" if ip_total else "0"
            ip_rows += IP_ROW.format(rank=rank, ip=ip, count=count, pct=pct)

        ip_chart_html = f'<div class="chart-card"><img src="data:image/png;base64,{ip_b64}" alt="IP Distribution" /></div>' if ip_b64 else ""
        ip_section = IP_SECTION.format(ip_chart=ip_chart_html, ip_rows=ip_rows)
    else:
        ip_section = "<section class=\"section\"><h2>Access by IP</h2><p style=\"color:#64748b\">No IP data recorded yet. IP tracking is active from this run onward.</p></section>"

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return HTML_TEMPLATE.format(
        subtitle=subtitle,
        total_runs=total,
        success_count=success_count,
        error_count=error_count,
        success_rate=success_rate_str,
        success_rate_class=success_rate_class,
        avg_duration=avg_duration,
        tracking_start=stats.get("tracking_start", "—"),
        chart_runs_per_day=runs_per_day_b64,
        verdict_section=verdict_section,
        ip_section=ip_section,
        generated_at=generated_at,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a MedContext analytics report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--url",
        default="https://medcontext.drjforrest.com",
        help="Base URL of the MedContext API (default: https://medcontext.drjforrest.com)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Rolling window in days (default: 30). Ignored when --all-time is set.",
    )
    parser.add_argument(
        "--all-time",
        action="store_true",
        help="Report all runs since the tracking start date (2026-03-01).",
    )
    parser.add_argument(
        "--output",
        default="medcontext_analytics.html",
        help="Output HTML file path (default: medcontext_analytics.html).",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Write the file but don't open it in a browser.",
    )

    args = parser.parse_args()

    print(f"Fetching analytics from {args.url} …", flush=True)
    stats = fetch_stats(args.url, days=args.days, all_time=args.all_time)

    print(f"Building report …", flush=True)
    html = build_report(stats)

    out = Path(args.output)
    out.write_text(html, encoding="utf-8")
    print(f"Report written to {out.resolve()}")

    if not args.no_open:
        webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()
