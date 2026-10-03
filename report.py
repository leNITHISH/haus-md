import analyze


def _header(title):
    print(f"\n{title}")
    print("-" * len(title))


def _season_table(rows):
    """rows: list of (seasonNumber, value, episode_count)."""
    for season, value, count in rows:
        print(f"  S{season:<3} {value:>6.2f}   ({count} eps)")


def _person_table(rows):
    """rows: list of (primaryName, episode_count, avg_rating)."""
    name_width = max((len(name) for name, _, _ in rows), default=0)
    for name, count, avg_rating in rows:
        print(f"  {name:<{name_width}}   {avg_rating:>5.2f}   ({count} eps)")


def _fmt(group, key):
    return f"{group[key]:.2f}" if key in group else "n/a"


def print_findings(con):
    _header("Early vs. late season rating")
    v1 = {part: avg for part, avg, _ in analyze.early_vs_late_v1(con)}
    v2 = {part: avg for part, avg, _ in analyze.early_vs_late_v2(con)}
    print(f"  take 1, flat cutoff (episode > 15):   early={_fmt(v1, 'early')}  late={_fmt(v1, 'late')}")
    print(f"  take 2, per-season midpoint (fixed):  early={_fmt(v2, 'early')}  late={_fmt(v2, 'late')}")
    print("  the gap mostly disappears once the split is fair -- take 1 was largely a measurement artifact")

    _header("Season averages")
    _season_table(analyze.season_averages(con))

    _header("Season volatility (rating stddev, most volatile first)")
    _season_table(analyze.season_volatility(con))

    _header("Votes per season")
    _season_table(analyze.votes_per_season(con))

    _header("Premiere vs. finale")
    for episode_type, avg_rating, count in analyze.premiere_vs_finale(con):
        print(f"  {episode_type:<9} {avg_rating:.2f}   ({count} eps)")

    _header("Correlations")
    print(f"  votes vs. rating:        r = {analyze.votes_rating_correlation(con):.3f}")
    print(f"  rating vs. watch order:  r = {analyze.overall_trend(con):.3f}")

    _header("Lowest-vote episodes")
    for tconst, season, episode, rating, votes in analyze.lowest_vote_episodes(con):
        print(f"  S{season}E{episode:<3} {tconst:<11} rating={rating:<5.1f} votes={votes}")

    _header("Biggest rating outliers (z-score vs. own season)")
    for tconst, season, episode, rating, z_score in analyze.season_rating_outliers(con):
        print(f"  S{season}E{episode:<3} {tconst:<11} rating={rating:<5.1f} z={z_score:+.2f}")

    _header("Director ratings (3+ episodes)")
    _person_table(analyze.director_ratings(con))

    _header("Writer ratings (3+ episodes)")
    _person_table(analyze.writer_ratings(con))
    print()
