import json

from fruitfly_brain.main import main


def test_dry_run_produces_traffic(capsys):
    code = main(["--dry-run", "--source", "mock", "--frames", "12", "--no-journal"])
    out = capsys.readouterr().out
    assert code == 0
    assert "fruitfly-brain" in out
    assert "frame" in out
    assert "done: 12 frames" in out
    body = json.loads(out.splitlines()[-2][out.splitlines()[-2].index("{") :])
    assert body["type"] == "motor_command"


def test_connectome_backend_runs(capsys):
    code = main(["--dry-run", "--source", "mock", "--brain", "connectome", "--frames", "10", "--no-journal"])
    assert code == 0
    assert "brain=connectome" in capsys.readouterr().out


def test_print_config_is_json(capsys):
    assert main(["--print-config"]) == 0
    cfg = json.loads(capsys.readouterr().out)
    assert cfg["camera"]["fps"] == 30


def test_bad_config_exits_with_2(tmp_path, capsys):
    p = tmp_path / "bad.yaml"
    p.write_text("motor:\n  max_command: 900\n", encoding="utf-8")
    assert main(["--config", str(p)]) == 2
    assert "config error" in capsys.readouterr().err


def test_journal_writes_lines(tmp_path, capsys):
    code = main(
        [
            "--dry-run",
            "--source",
            "mock",
            "--frames",
            "12",
            "--config",
            str(_write_config(tmp_path)),
        ]
    )
    assert code == 0
    lines = list((tmp_path / "runs").glob("bridge-*.jsonl"))
    assert lines, "journal file was not created"
    rows = [json.loads(line) for line in lines[0].read_text().splitlines()]
    assert rows and set(rows[0]) >= {"frame", "event", "t"}


def _write_config(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text(
        "log:\n  dir: %s\n  every_n_frames: 2\n" % (tmp_path / "runs"),
        encoding="utf-8",
    )
    return p
