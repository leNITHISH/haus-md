import logging

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config

log = logging.getLogger(__name__)


def plot_rolling_average(con, out_path=None):
    """Plot the 5-episode rolling average rating across the whole series
    in watch order, to visually spot rating arcs (e.g. the Season 4
    finale / "Amber" arc)."""

    out_path = out_path or (config.OUTPUT_DIR / "rolling_avg.png")
    rows = con.sql("""
        SELECT seasonNumber, episodeNumber, rolling_avg
        FROM house_rolling
        ORDER BY seasonNumber, episodeNumber;
    """).fetchall()

    watch_order = list(range(1, len(rows) + 1))
    rolling_avg = [r[2] for r in rows]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(watch_order, rolling_avg)
    ax.set_xlabel("Episode (watch order)")
    ax.set_ylabel("5-episode rolling average rating")
    ax.set_title("House, M.D. rating over time")
    fig.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    log.info("wrote %s", out_path)
    return out_path
