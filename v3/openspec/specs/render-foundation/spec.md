# Spec: Render Foundation

## Purpose

Provides the shared rendering subsystem that turns a resolved data object (the
source) into a file in one of several Formats. It sits below the CLI and above the
data layer, exposing one generic `render()` seam driven by data records — the
Format and Product registries, two Jinja environments, and two derivations
(Markdown→HTML, LaTeX→PDF) — so each gameplay-reference Product plugs in by
contributing templates only.

## Requirements

### Requirement: Render seam

The system SHALL expose a single entry point
`render(product, source, fmt, *, name, out=None) -> Path` that renders exactly
one source object to exactly one file and returns the written path. It SHALL be a
generic pipeline parameterized by the Format and Product records — it MUST NOT
contain per-product or per-format branching code.

#### Scenario: Render one source to one file

- **WHEN** `render` is called with a registered Product, a source object, a
  registered Format, and a `name`
- **THEN** the source is rendered through the Format's family environment and the
  written file path is returned

#### Scenario: Source passed to a dumb template

- **WHEN** a template is rendered
- **THEN** the resolved source object is passed in whole under a fixed variable
  and the template performs no lookups or computation

### Requirement: Format registry

The system SHALL provide a `Format(name, extension, family, post_step)` record and
register exactly four Formats: `markdown` (ext `md`, family `markdown`, no
post-step), `html` (ext `html`, family `markdown`, post-step `md_to_html`),
`latex` (ext `tex`, family `latex`, no post-step), and `pdf` (ext `pdf`, family
`latex`, post-step `latex_to_pdf`). Formats SHALL be looked up by name.

#### Scenario: Look up a registered Format

- **WHEN** a Format is requested by one of the four names
- **THEN** its extension, family, and optional post-step are returned

#### Scenario: Unknown Format name

- **WHEN** a Format is requested by a name that is not registered
- **THEN** the system raises a clear error

### Requirement: Product registry

The system SHALL provide a `Product` record type and a registry mechanism, and
SHALL register **zero** concrete Products in this foundation. A Product SHALL NOT
be bound to a single template family; the `(product, family)` pair locates
templates.

#### Scenario: Registry mechanism present, no products registered

- **WHEN** the foundation is loaded
- **THEN** the Product registry exists and is empty, ready for product issues to
  register their own records

### Requirement: Missing template combinations fail lazily

The system SHALL NOT pre-validate the product-by-family matrix. A missing
`(product, family)` template combination SHALL surface only when that combination
is rendered.

#### Scenario: Requesting an unauthored format

- **WHEN** `render` is called for a `(product, family)` pair that has no template
- **THEN** a `TemplateNotFound`-style error is raised at render time only

### Requirement: Two Jinja environments

The system SHALL provide two Jinja2 environments built by an injectable factory
`make_environments(templates_root)` that defaults `templates_root` to
`config.paths.templates` but accepts an override. The **Markdown** environment
SHALL use stock delimiters and `autoescape=False`. The **LaTeX** environment SHALL
use `\VAR{}` / `\BLOCK{}` delimiters, `autoescape=False`, with `trim_blocks` and
`lstrip_blocks` enabled. Both SHALL load templates from `templates/<family>/` with
entry template `<product>/main.<ext>.jinja`.

#### Scenario: Markdown environment does not HTML-escape

- **WHEN** a value containing HTML-special characters is interpolated by a
  Markdown-family template
- **THEN** the characters appear unescaped in the emitted Markdown text

#### Scenario: LaTeX environment uses custom delimiters

- **WHEN** a LaTeX-family template uses `\VAR{}` and `\BLOCK{}`
- **THEN** they are interpreted as expression and statement delimiters and stock
  `{{ }}` braces are left literal

#### Scenario: Injected templates root

- **WHEN** `make_environments` is called with an explicit `templates_root`
- **THEN** the environments load templates from that root instead of the config
  default

### Requirement: Markdown-to-HTML derivation

The system SHALL provide `md_to_html` that converts Markdown text to HTML using
`markdown-it-py` with table support enabled, and wraps the result in a minimal
standalone HTML5 document (doctype, `<meta charset>`, `<title>`, a small embedded
default stylesheet).

#### Scenario: Tables render

- **WHEN** the Markdown input contains a GFM table
- **THEN** the output contains an HTML `<table>`

#### Scenario: Standalone document

- **WHEN** `md_to_html` runs
- **THEN** the output is a full HTML document with a doctype and charset, not a
  bare fragment

### Requirement: LaTeX-to-PDF derivation

The system SHALL provide `latex_to_pdf` that compiles LaTeX to PDF using the
engine named by `config.render.latex.engine`, running the engine twice in a
temporary directory with `-interaction=nonstopmode -halt-on-error`, and copying
only the resulting `.pdf` to the output path. No transient files SHALL touch the
repository or the output tree.

#### Scenario: Only the PDF survives

- **WHEN** compilation succeeds
- **THEN** only the `.pdf` is copied to the output path and the temporary
  directory (with its `.aux`/`.log`) is removed

#### Scenario: Engine binary missing

- **WHEN** the configured engine binary is not on `PATH`
- **THEN** a clear error names the missing tool and notes that only the `pdf`
  Format requires it

#### Scenario: Compilation fails

- **WHEN** the engine exits non-zero
- **THEN** an error is raised that includes the tail of the engine log

### Requirement: Output path resolution and write behavior

The system SHALL resolve the default output path as
`output_root / product / f"{name}.{extension}"`, where `output_root` is an
overridable argument defaulting to `config.paths.output`. An explicit `out`
argument SHALL override the full file path. `render` SHALL create parent
directories and overwrite any existing file silently.

#### Scenario: Default path layout

- **WHEN** `render` is called without `out`
- **THEN** the file is written to `output_root/<product>/<name>.<ext>` with parent
  directories created

#### Scenario: Explicit out override

- **WHEN** `render` is called with an explicit `out` file path
- **THEN** the file is written exactly there, ignoring the default layout

#### Scenario: Silent overwrite

- **WHEN** the target file already exists
- **THEN** it is overwritten without prompting

### Requirement: Configuration additions

The system SHALL add `paths.output` (default `{project_path}/output`) to the paths
config and a nested `[render.latex].engine` setting (default `pdflatex`) exposed
as `config.render.latex.engine`. The `output/` directory SHALL be gitignored.

#### Scenario: Output path available

- **WHEN** the configuration is loaded
- **THEN** `config.paths.output` resolves to the configured output directory

#### Scenario: Engine configurable

- **WHEN** `config.render.latex.engine` is set to another engine name
- **THEN** `latex_to_pdf` invokes that binary

### Requirement: CLI render scaffold

The system SHALL register an empty `spf render` command group wired like the
existing `army`/`race`/`rules` groups, and provide a reusable `--format` /
`--out` parameter set whose `--format` choices derive from the Format registry
(default `pdf`). No product subcommand and no dummy command SHALL be added in this
foundation.

#### Scenario: Empty render group present

- **WHEN** `spf render` is invoked with no subcommand
- **THEN** help is shown and no product subcommands are listed

#### Scenario: Format choices come from the registry

- **WHEN** the `--format` option is offered
- **THEN** its allowed values are exactly the registered Format names with `pdf`
  as default

### Requirement: Direct dependencies

The system SHALL declare `jinja2` and `markdown-it-py` as direct project
dependencies. `pdflatex`/`xelatex` SHALL remain an external system prerequisite,
not a Python dependency.

#### Scenario: Libraries are direct dependencies

- **WHEN** the project dependencies are inspected
- **THEN** `jinja2` and `markdown-it-py` appear as direct dependencies
