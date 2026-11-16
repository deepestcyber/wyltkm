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


def test_icon_commands(tmp_path):
    runner = CliRunner()
    r = runner.invoke(main, ["icons"])
    assert {"fa", "carbon", "40c3", "attraktor"} <= {line.split()[0] for line in r.output.splitlines()}
    r = runner.invoke(main, ["icons", "search", "cat", "-n", "3"])
    assert r.output.splitlines()[0] == "fa:solid/cat  Cat"
    r = runner.invoke(main, ["icons", "list", "40c3", "logos"])
    assert r.exit_code == 0 and "40c3:logos/40c3-logo-a" in r.output and "citizens" not in r.output
    assert runner.invoke(main, ["icons", "list", "nope"]).exit_code == 3
    out = tmp_path / "i.svg"
    r = runner.invoke(main, ["icons", "show", "fa:solid/cat", "-c", "#ff0000", "-o", str(out)])
    assert r.exit_code == 0 and "#ff0000" in out.read_text() and "CC-BY-4.0" in r.stderr
    assert runner.invoke(main, ["icons", "show", "fa:solid/cat", "-c", "red"]).exit_code == 1


def test_icon_file(tmp_path):
    icon = tmp_path / "i.svg"
    icon.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><path d="M0 0H1V1Z"/></svg>')
    runner = CliRunner()
    r = runner.invoke(main, ["render", "x", "--icon-file", str(icon), "--licences"])
    assert r.exit_code == 0 and "uploaded by the user" in r.stderr
    r = runner.invoke(main, ["render", "x", "--icon-file", str(icon), "-i", "fa:solid/cat"])
    assert r.exit_code == 1
    icon.write_text("<!DOCTYPE x [<!ENTITY a 'b'>]><svg>&a;</svg>")
    assert runner.invoke(main, ["render", "x", "--icon-file", str(icon)]).exit_code == 1
