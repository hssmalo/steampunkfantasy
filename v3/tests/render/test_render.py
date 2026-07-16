"""Tests for the spf.render foundation."""

import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from jinja2 import TemplateNotFound

from spf.config import config
from spf.frontends.cli.render import DEFAULT_FORMAT, RenderOpts
from spf.render import Product, render
from spf.render.derivations import RenderError, latex_to_pdf, md_to_html
from spf.render.environments import make_environments
from spf.render.formats import FORMATS, get_format
from spf.render.products import PRODUCTS, get_product, register_product

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


# --- 7.2 md_to_html ---------------------------------------------------------


def test_md_to_html_renders_table() -> None:
    markdown = "| A | B |\n| - | - |\n| 1 | 2 |\n"
    assert "<table>" in md_to_html(markdown)


def test_md_to_html_is_standalone_document() -> None:
    html = md_to_html("# Title\n")
    assert html.lstrip().startswith("<!DOCTYPE html>")
    assert 'charset="utf-8"' in html


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


@pytest.mark.skipif(shutil.which(ENGINE) is None, reason=f"{ENGINE} not installed")
def test_render_pdf_end_to_end(
    tmp_path: Path, product: Product, *, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list[Path] = []
    real_tempdir = tempfile.TemporaryDirectory

    def tracking_tempdir() -> tempfile.TemporaryDirectory[str]:
        temp = real_tempdir()
        captured.append(Path(temp.name))
        return temp

    monkeypatch.setattr(tempfile, "TemporaryDirectory", tracking_tempdir)

    out = render(
        product,
        FakeSource(),
        fmt=get_format("pdf"),
        name="sample",
        templates_root=FIXTURES,
        output_root=tmp_path,
    )
    assert out == tmp_path / "_test" / "sample.pdf"
    assert out.stat().st_size > 0
    assert captured
    assert not captured[0].exists()


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
