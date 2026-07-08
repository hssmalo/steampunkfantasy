## 1. Dependencies & config

- [x] 1.1 Use `uv add` to promote `jinja2` and `markdown-it-py` to direct `[project.dependencies]` in `pyproject.toml`. Do not manually edit the file
- [x] 1.2 Add `output = "{project_path}/output"` under `[paths]` in `configs/spf.toml`
- [x] 1.3 Add `[render.latex]` with `engine = "pdflatex"` in `configs/spf.toml`
- [x] 1.4 Add `output: Path` to `PathsConfig` in `src/spf/schemas/config.py`
- [x] 1.5 Add `RenderConfig` → `LatexConfig(engine: str = "pdflatex")` and wire `render` onto `SteamPunkFantasyConfig`
- [x] 1.6 Add `output/` to `.gitignore`

## 2. Format & Product registries

- [x] 2.1 Create `src/spf/render/__init__.py` exposing `render`, `Format`, `Product`
- [x] 2.2 Implement `Format(name, extension, family, post_step)` record + `FORMATS` dict + register/lookup helper in `formats.py`
- [x] 2.3 Register the four Formats (`markdown`, `html`→`md_to_html`, `latex`, `pdf`→`latex_to_pdf`) — leave post-steps as forward references until section 4
- [x] 2.4 Implement `Product` record type + `PRODUCTS` dict + register/lookup helper in `products.py`; register zero concrete products

## 3. Jinja environments

- [x] 3.1 Implement `make_environments(templates_root=config.paths.templates)` in `environments.py` returning `{family: Environment}`
- [x] 3.2 Configure the Markdown env: stock delimiters, `autoescape=False`, `FileSystemLoader` rooted at `templates/markdown/`
- [x] 3.3 Configure the LaTeX env: `\VAR{}`/`\BLOCK{}` delimiters, `autoescape=False`, `trim_blocks` + `lstrip_blocks`, loader rooted at `templates/latex/`
- [x] 3.4 Create empty `templates/markdown/` and `templates/latex/` subtrees (leave legacy `templates/*.tex` untouched)

## 4. Derivations

- [x] 4.1 Implement `md_to_html` in `derivations.py`: `markdown-it-py` with tables enabled, wrapping output in a minimal standalone HTML5 document
- [x] 4.2 Implement `latex_to_pdf`: compile in a `tempfile.TemporaryDirectory()` with the configured engine, `-interaction=nonstopmode -halt-on-error`, run twice, copy only the `.pdf`
- [x] 4.3 Add missing-binary handling (clear error naming the tool, noting only `pdf` needs it)
- [x] 4.4 Add non-zero-exit handling (raise with the tail of the engine log)
- [x] 4.5 Wire the two post-steps into the Format registry from section 2

## 5. Render pipeline

- [x] 5.1 Implement `render(product, source, fmt, *, name, out=None, templates_root=None, output_root=None) -> Path` in `pipeline.py`
- [x] 5.2 Resolve the environment by `fmt.family`, load `<product>/main.<ext>.jinja`, render the source under a fixed variable
- [x] 5.3 Apply `fmt.post_step` when present; otherwise use the rendered text directly
- [x] 5.4 Resolve the output path (`output_root/<product>/<name>.<ext>` or explicit `out`), `mkdir(parents=True, exist_ok=True)`, write with silent overwrite, return the path

## 6. CLI scaffold

- [x] 6.1 Register an empty `spf render` cyclopts sub-App in `cli/main.py`, wired like `army`/`race`/`rules`
- [x] 6.2 Add `cli/render.py` with an `add_commands(app)` hook and a reusable `RenderOpts(format, out)` parameter set
- [x] 6.3 Derive `--format` choices from the Format registry with `pdf` as default

## 7. Tests

- [x] 7.1 Unit-test both environments: Markdown non-escaping, LaTeX `\VAR{}`/`\BLOCK{}` delimiters, injected `templates_root`
- [x] 7.2 Unit-test `md_to_html`: table renders, output is a standalone document
- [x] 7.3 Unit-test `latex_to_pdf` behavior (missing-binary error; compile-failure log tail) with `skipif` where the engine is required
- [x] 7.4 Add fixture templates under `tests/fixtures/templates/<family>/_test/main.*.jinja` and a fake source
- [x] 7.5 End-to-end `render()` test through markdown and latex asserting the file lands at the expected `output/...` path
- [x] 7.6 PDF end-to-end test gated by `@pytest.mark.skipif(shutil.which(engine) is None)`; assert non-empty `.pdf` and temp-dir cleanup
- [x] 7.7 Test that `config.paths.output` and `config.render.latex.engine` resolve

## 8. Quality gates

- [x] 8.1 Run `just check` (format, lint, type-check, spell-check) and the test suite; fix any failures
