"""The render seam: one generic pipeline for every Product and Format.

`render` looks up the family environment for the Format, loads the Product's
`main.<ext>.jinja` template, renders the whole source object into it, applies
the Format's post-step if any, and writes exactly one file. It contains no
per-product or per-format branching — behavior comes entirely from the Format and
Product records.
"""

from collections.abc import Callable
from functools import partial
from pathlib import Path, PurePath

from spf.config import config
from spf.render.environments import make_environments, relative_to
from spf.render.formats import FAMILY_TEMPLATE_EXT, Format
from spf.render.products import Product

# The fixed variable name the source object is bound to inside every template.
SOURCE_VAR = "source"


def render(  # noqa: PLR0913  the seam's parameters are fixed by the render-foundation spec
    product: Product,
    source: object,
    *,
    fmt: Format,
    name: str,
    out: Path | None = None,
    templates_root: Path | None = None,
    output_root: Path | None = None,
    image_src: Callable[[PurePath], str] | None = None,
) -> Path:
    """Render one `source` to one file and return the written path.

    The template `<product>/main.<ext>.jinja` from the Format's family is
    rendered with `source` bound to `SOURCE_VAR`. A missing template for the requested
    `(product, family)` pair surfaces as Jinja's
    `TemplateNotFound` here, at render time only. The Format's post-step, when
    present, produces the final content; otherwise the rendered text is written
    directly. The output path is `out` when given, else
    `output_root/<product>/<name>.<ext>`. Parent directories are created and any
    existing file is overwritten silently.
    """
    # Resolved before the template runs: the default image spelling is relative
    # to where this document lands.
    if out is None:
        root = output_root if output_root is not None else config.paths.output
        out = root / product.name / f"{name}.{fmt.extension}"

    environments = make_environments(templates_root)
    # Bound per render rather than per family: which spelling an Asset takes is
    # the destination's business, and one template serves both destinations.
    spelling = (
        image_src if image_src is not None else partial(relative_to, start=out.parent)
    )
    environments["markdown"].filters["image_src"] = spelling
    template_ext = FAMILY_TEMPLATE_EXT[fmt.family]
    template = environments[fmt.family].get_template(
        f"{product.name}/main.{template_ext}.jinja"
    )
    rendered = template.render({SOURCE_VAR: source})
    content = fmt.post_step(rendered) if fmt.post_step is not None else rendered

    out.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        out.write_bytes(content)
    else:
        out.write_text(content, encoding="utf-8")
    return out
