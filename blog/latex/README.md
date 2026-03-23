# LaTeX Blog Sources

Put standalone LaTeX blog posts in this directory using the same date-slug naming
scheme as the generated post:

- `YYYYMMDD-your-post-slug.tex` -> `blog/YYYYMMDD-your-post-slug.qmd`

The converter script expects optional YAML metadata at the top of each `.tex` file
as `%`-commented front matter:

```tex
% ---
% title: "Post title"
% date: 2026-03-18
% categories: [notes, math]
% ---
```

Then convert with:

```bash
python tools/convert_latex_posts.py
```

Custom side notes are supported with:

```tex
\begin{sidework}
This will appear in Quarto's margin column.
\end{sidework}
```

Those blocks are converted to:

```markdown
::: column-margin
This will appear in Quarto's margin column.
:::
```
