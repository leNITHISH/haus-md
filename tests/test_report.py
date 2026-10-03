import report


def test_print_findings_runs_and_prints(crew_con, capsys):
    report.print_findings(crew_con)
    captured = capsys.readouterr()
    assert "Season averages" in captured.out
    assert "Director ratings" in captured.out
