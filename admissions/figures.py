"""Charts for the README and the case study page, in English and Portuguese."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

PAPER, INK, FAINT, RULE, ACCENT = "#f7f5f0", "#1c1b18", "#8a857a", "#d9d4c8", "#7d2e2e"

TEXT = {
    "en": {
        "lag_title": "Brazil, all states: the same admissions counted two ways",
        "lag_service": "by month of admission",
        "lag_processing": "by month of processing",
        "lag_y": "Hospital admissions per month (thousands)",
        "lag_note": "latest months still\nbeing reported",
        "h_title": "Backtest, 27 states, 33 forecast origins (Jan 2023 to Sep 2025)",
        "h_x": "Months ahead",
        "h_y": "Error, % of admissions (WAPE)",
        "h_naive": "Same month last year",
        "h_raw": "SARIMA, pandemic left in",
        "h_final": "SARIMA, pandemic masked + working days",
        "fc_title": "Paraná: forecast for the next 12 months with an 80% band",
        "fc_y": "Hospital admissions per month (thousands)",
        "fc_hist": "observed",
        "fc_mean": "forecast",
        "fc_band": "80% band",
        "fc_masked": "pandemic, left out of the fit",
    },
    "pt": {
        "lag_title": "Brasil, todos os estados: as mesmas internações contadas de dois jeitos",
        "lag_service": "pelo mês da internação",
        "lag_processing": "pelo mês do processamento",
        "lag_y": "Internações por mês (milhares)",
        "lag_note": "últimos meses ainda\nsendo registrados",
        "h_title": "Backtest, 27 estados, 33 pontos de partida (jan/2023 a set/2025)",
        "h_x": "Meses à frente",
        "h_y": "Erro, % das internações (WAPE)",
        "h_naive": "Mesmo mês do ano anterior",
        "h_raw": "SARIMA, com a pandemia",
        "h_final": "SARIMA, pandemia mascarada + dias úteis",
        "fc_title": "Paraná: previsão dos próximos 12 meses com faixa de 80%",
        "fc_y": "Internações por mês (milhares)",
        "fc_hist": "observado",
        "fc_mean": "previsão",
        "fc_band": "faixa de 80%",
        "fc_masked": "pandemia, fora do ajuste",
    },
}


def _style(ax, title):
    fig = ax.figure
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(RULE)
    ax.tick_params(colors=INK, labelsize=10)
    ax.grid(axis="y", color=RULE, linewidth=0.8, alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_title(title, loc="left", color=FAINT, fontsize=13, pad=12)


def reporting_lag(service: pd.Series, processing: pd.Series, out: Path, lang: str) -> None:
    t = TEXT[lang]
    s, p = service / 1e3, processing / 1e3
    fig, ax = plt.subplots(figsize=(10, 4.9), dpi=146)
    _style(ax, t["lag_title"])
    ax.plot(p.index, p.values, color=INK, lw=2, label=t["lag_processing"])
    ax.plot(s.index, s.values, color=ACCENT, lw=2, label=t["lag_service"])
    ax.annotate(t["lag_note"], xy=(s.index[-1], s.values[-1]), xytext=(-150, 10),
                textcoords="offset points", color=ACCENT, fontsize=10,
                arrowprops=dict(arrowstyle="-", color=ACCENT, lw=0.8))
    ax.set_ylabel(t["lag_y"], color=INK)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
    ax.legend(frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig(out, facecolor=PAPER)
    plt.close(fig)


def error_by_horizon(by_h: pd.DataFrame, out: Path, lang: str) -> None:
    t = TEXT[lang]
    fig, ax = plt.subplots(figsize=(10, 4.9), dpi=146)
    _style(ax, t["h_title"])
    x = by_h.index
    ax.plot(x, 100 * by_h["seasonal_naive"], color=FAINT, lw=2, marker="o", ms=4, label=t["h_naive"])
    ax.plot(x, 100 * by_h["sarima_raw"], color=INK, lw=1.4, ls="--", label=t["h_raw"])
    ax.plot(x, 100 * by_h["sarima_masked_wd"], color=ACCENT, lw=2.4, marker="o", ms=4, label=t["h_final"])
    ax.set_xticks(list(x))
    ax.set_xlabel(t["h_x"], color=INK)
    ax.set_ylabel(t["h_y"], color=INK)
    ax.set_ylim(0, None)
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(out, facecolor=PAPER)
    plt.close(fig)


def state_forecast(history: pd.Series, fc: pd.DataFrame, pandemic: tuple[str, str],
                   out: Path, lang: str) -> None:
    t = TEXT[lang]
    h = history / 1e3
    fig, ax = plt.subplots(figsize=(10, 4.9), dpi=146)
    _style(ax, t["fc_title"])
    ax.axvspan(pd.Timestamp(pandemic[0]), pd.Timestamp(pandemic[1]), color=RULE, alpha=0.45, lw=0)
    ax.text(pd.Timestamp(pandemic[0]), h.max() * 1.01, t["fc_masked"], color=FAINT, fontsize=9, va="bottom")
    ax.plot(h.index, h.values, color=INK, lw=1.6, label=t["fc_hist"])
    ax.fill_between(fc.index, fc["lo80"] / 1e3, fc["hi80"] / 1e3, color=ACCENT, alpha=0.18, lw=0, label=t["fc_band"])
    ax.plot(fc.index, fc["forecast"] / 1e3, color=ACCENT, lw=2.2, label=t["fc_mean"])
    ax.set_ylabel(t["fc_y"], color=INK)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig(out, facecolor=PAPER)
    plt.close(fig)
