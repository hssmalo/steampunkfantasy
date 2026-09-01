"""Tests for the spf.render foundation."""

import shutil
from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath

import pytest
from jinja2 import TemplateNotFound

from spf.config import config
from spf.frontends.cli.render import DEFAULT_FORMAT, RenderOpts
from spf.render import Product, render
from spf.render.derivations import RenderError, latex_to_pdf, md_to_html
from spf.render.environments import make_environments, posix_path, relative_to
from spf.render.formats import FORMATS, get_format
from spf.render.products import PRODUCTS, get_product, register_product
from spf.version import spf_version

FIXTURES = Path(__file__).parent.parent / "fixtures" / "templates"
ENGINE = config.render.latex.engine


@dataclass
class FakeSource:
    """A stand-in source object for exercising the pipeline."""

    title: str = "Test Rendering"
    note: str = "A & B < C"
    rows: list[tuple[str, str]] = field(
        default_factory=lambda: [("Speed", "fast"), ("Size", "Small")]
    )


# --- 7.1 Environments -------------------------------------------------------


def test_markdown_environment_does_not_escape() -> None:
    envs = make_environments(templates_root=FIXTURES)
    result = envs["markdown"].from_string("{{ value }}").render(value="a & b <c>")
    assert result == "a & b <c>"


def test_latex_environment_custom_delimiters() -> None:
    envs = make_environments(templates_root=FIXTURES)
    template = envs["latex"].from_string(r"\VAR{x} then {{ y }}")
    result = template.render(x=1, y=2)
    assert result == "1 then {{ y }}"


def test_latex_environment_block_delimiter() -> None:
    envs = make_environments(templates_root=FIXTURES)
    template = envs["latex"].from_string(
        r"\BLOCK{ for n in nums }\VAR{n}\BLOCK{ endfor }"
    )
    assert template.render(nums=[1, 2, 3]) == "123"


def test_injected_templates_root_loads_fixture() -> None:
    envs = make_environments(templates_root=FIXTURES)
    template = envs["markdown"].get_template("_test/main.md.jinja")
    assert "Name" in template.render(source=FakeSource())


# --- Path filters: separators must survive Markdown and LaTeX ---------------


def test_relative_to_climbs_out_of_the_output_directory() -> None:
    assert (
        relative_to(Path("/repo/assets/elf/images/art.png"), Path("/repo/output/rules"))
        == "../../assets/elf/images/art.png"
    )


def test_relative_to_emits_forward_slashes_on_windows() -> None:
    # CommonMark reads a backslash as an escape, so a Windows-separated
    # `..\..\art.png` renders as `....%5Cart.png` and the image 404s. On
    # Windows a `Path` *is* a `WindowsPath`, of which `PureWindowsPath` is the
    # pure flavor — so passing one exercises the real separator behavior.
    relative = relative_to(
        PureWindowsPath(r"C:\repo\assets\elf\images\art.png"),
        PureWindowsPath(r"C:\repo\output\army-rules"),
    )

    assert relative == "../../assets/elf/images/art.png"


def test_posix_path_emits_forward_slashes_for_a_windows_path() -> None:
    # A backslash opens a control sequence in LaTeX, so
    # `\includegraphics{C:\repo\art.png}` compiles as `\r` and `\a`, not a name.
    windows = PureWindowsPath(r"C:\repo\assets\elf\images\art.png")

    assert posix_path(windows) == "C:/repo/assets/elf/images/art.png"


# --- 7.2 md_to_html ---------------------------------------------------------


def test_md_to_html_renders_table() -> None:
    markdown = "| A | B |\n| - | - |\n| 1 | 2 |\n"
    assert "<table>" in md_to_html(markdown)


def test_md_to_html_is_standalone_document() -> None:
    html = md_to_html("# Title\n")
    assert html.lstrip().startswith("<!DOCTYPE html>")
    assert 'charset="utf-8"' in html


def test_md_to_html_constrains_image_width() -> None:
    # Markdown has no sizing syntax, so a committed Image Asset would otherwise
    # render at its native pixel width.
    html = md_to_html("![art](/assets/goblin/images/art.png)\n")
    assert '<img src="/assets/goblin/images/art.png"' in html
    assert "max-width: 20rem" in html


# --- 7.3 latex_to_pdf behavior ---------------------------------------------


def test_latex_to_pdf_missing_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config.render.latex, "engine", "definitely-not-a-real-engine")
    with pytest.raises(RenderError) as excinfo:
        latex_to_pdf(r"\documentclass{article}\begin{document}x\end{document}")
    message = str(excinfo.value)
    assert "definitely-not-a-real-engine" in message
    assert "pdf" in message


@pytest.mark.skipif(shutil.which(ENGINE) is None, reason=f"{ENGINE} not installed")
def test_latex_to_pdf_compile_failure_includes_log_tail() -> None:
    with pytest.raises(RenderError) as excinfo:
        latex_to_pdf(r"\documentclass{article}\begin{document}\undefinedmacro")
    assert ENGINE in str(excinfo.value)


# --- 7.5 End-to-end text formats -------------------------------------------


@pytest.fixture
def product() -> Product:
    return Product(name="_test")


def test_render_markdown_to_expected_path(tmp_path: Path, product: Product) -> None:
    out = render(
        product,
        FakeSource(),
        fmt=get_format("markdown"),
        name="sample",
        templates_root=FIXTURES,
        output_root=tmp_path,
    )
    assert out == tmp_path / "_test" / "sample.md"
    assert out.exists()
    assert "Test Rendering" in out.read_text(encoding="utf-8")


def test_render_latex_to_expected_path(tmp_path: Path, product: Product) -> None:
    out = render(
        product,
        FakeSource(),
        fmt=get_format("latex"),
        name="sample",
        templates_root=FIXTURES,
        output_root=tmp_path,
    )
    assert out == tmp_path / "_test" / "sample.tex"
    assert r"\section*{Test Rendering}" in out.read_text(encoding="utf-8")


def test_render_explicit_out_overrides_layout(tmp_path: Path, product: Product) -> None:
    target = tmp_path / "custom" / "file.md"
    out = render(
        product,
        FakeSource(),
        fmt=get_format("markdown"),
        name="ignored",
        out=target,
        templates_root=FIXTURES,
    )
    assert out == target
    assert target.exists()


def test_render_silently_overwrites(tmp_path: Path, product: Product) -> None:
    target = tmp_path / "file.md"
    target.write_text("stale", encoding="utf-8")
    render(
        product,
        FakeSource(),
        fmt=get_format("markdown"),
        name="ignored",
        out=target,
        templates_root=FIXTURES,
    )
    assert "stale" not in target.read_text(encoding="utf-8")


def test_render_missing_template_fails_lazily(tmp_path: Path) -> None:
    with pytest.raises(TemplateNotFound):
        render(
            Product(name="_absent"),
            FakeSource(),
            fmt=get_format("markdown"),
            name="sample",
            templates_root=FIXTURES,
            output_root=tmp_path,
        )


# --- 7.6 PDF end-to-end (gated) --------------------------------------------


# --- Registries -------------------------------------------------------------


def test_format_registry_has_four_formats() -> None:
    assert set(FORMATS) == {"markdown", "html", "latex", "pdf"}
    assert get_format("html").post_step is md_to_html
    assert get_format("markdown").post_step is None


def test_unknown_format_raises() -> None:
    with pytest.raises(ValueError, match="Unknown format"):
        get_format("nope")


def test_product_registry_contains_cards_product() -> None:
    # The Order Card product registers itself at import (spf.frontends.cli.render).
    assert PRODUCTS["cards"] == Product(name="cards")


def test_product_registry_registers_and_looks_up() -> None:
    try:
        registered = register_product(Product(name="_probe"))
        assert get_product("_probe") is registered
    finally:
        PRODUCTS.pop("_probe", None)


# --- 7.7 Config resolves ----------------------------------------------------


def test_config_output_and_engine_resolve() -> None:
    assert isinstance(config.paths.output, Path)
    assert config.paths.output.name == "output"
    assert isinstance(config.render.latex.engine, str)
    assert config.render.latex.engine


def test_format_choices_derive_from_registry() -> None:
    assert DEFAULT_FORMAT == "pdf"
    assert RenderOpts().format == "pdf"
    assert DEFAULT_FORMAT in FORMATS


# --- Version global ---------------------------------------------------------


def test_environments_expose_the_version_to_both_families() -> None:
    envs = make_environments(templates_root=FIXTURES)
    assert envs["markdown"].globals["spf_version"] == spf_version()
    assert envs["latex"].globals["spf_version"] == spf_version()


def test_markdown_template_can_reference_the_version() -> None:
    envs = make_environments(templates_root=FIXTURES)
    assert envs["markdown"].from_string("{{ spf_version }}").render() == spf_version()


def test_latex_template_can_reference_the_version() -> None:
    envs = make_environments(templates_root=FIXTURES)
    assert envs["latex"].from_string(r"\VAR{spf_version}").render() == spf_version()
