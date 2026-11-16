from click.testing import CliRunner

from wyltkm.cli import main


def test_render_svg_to_stdout():
    r = CliRunner().invoke(main, ["render", "https://example.org", "-t", "A", "-t", "B",
                                  "-i", "none"])
    assert r.exit_code == 0, r.output
    assert r.stdout.startswith("<?xml")


def test_render_png_file(tmp_path):
    out = tmp_path / "x.png"
    r = CliRunner().invoke(main, ["render", "x", "-o", str(out), "--no-licence-metadata"])
    assert r.exit_code == 0
    assert out.read_bytes().startswith(b"\x89PNG")


def test_errors():
    runner = CliRunner()
    assert runner.invoke(main, ["render", "x", "-d", "nope"]).exit_code == 3
    assert runner.invoke(main, ["render", "x", "-i", "fa:solid/nope"]).exit_code == 3
    assert runner.invoke(main, ["render", "x", "-s", "main"]).exit_code == 1
    assert runner.invoke(main, ["render", "x", "-w", "10"]).exit_code == 2


def test_licence_note_and_list():
    r = CliRunner().invoke(main, ["render", "x", "-i", "fa:solid/cat", "--licences"])
    assert "CC-BY-4.0" in r.stderr
    r = CliRunner().invoke(main, ["licences"])
    assert r.exit_code == 0 and "OFL-1.1" in r.output


def test_inspect_commands():
    runner = CliRunner()
    assert "attraktor" in runner.invoke(main, ["designs"]).output
    r = runner.invoke(main, ["designs", "show", "38c3-lighter"])
    assert r.exit_code == 0 and "SpaceGrotesk-Regular.otf" in r.output
    assert runner.invoke(main, ["designs", "show", "nope"]).exit_code == 3
    assert "fa" in runner.invoke(main, ["icons"]).output


def test_designs_schemes_and_preview(tmp_path):
    runner = CliRunner()
    assert "schemes: green, teal" in runner.invoke(main, ["designs"]).output
    r = runner.invoke(main, ["designs", "show", "40c3"])
    assert "schemes (default green)" in r.output and "contrast" in r.output
    out = tmp_path / "p.png"
    r = runner.invoke(main, ["designs", "show", "40c3", "--preview", "pink", "-o", str(out)])
    assert r.exit_code == 0 and out.read_bytes().startswith(b"\x89PNG")
    r = runner.invoke(main, ["designs", "show", "38c3", "--preview"])
    assert r.exit_code == 0 and r.stdout.startswith("<?xml")
    r = runner.invoke(main, ["render", "x", "-d", "40c3", "-s", "light"])
    assert r.exit_code == 0


def test_config_and_fonts_commands():
    runner = CliRunner()
    r = runner.invoke(main, ["config"])
    assert r.exit_code == 0 and "none (defaults)" in r.output and "missing" in r.output
    r = runner.invoke(main, ["fonts"])
    assert r.exit_code == 0 and "Hack-Regular.ttf" in r.output and "38c3-lighter" in r.output


def test_broken_config(tmp_path, monkeypatch):
    path = tmp_path / "c.toml"
    path.write_text("nope = 1\n")
    monkeypatch.setenv("WYLTKM_CONFIG", str(path))
    r = CliRunner().invoke(main, ["designs"])
    assert r.exit_code == 4 and "unknown keys" in r.output
