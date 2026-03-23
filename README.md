# clarkmiyamoto.github.io

## Locally preview website

```
quarto preview
```

## Author blog posts in LaTeX

1. Add or edit a standalone `.tex` post in `blog/latex/` using date-slug naming:
   `YYYYMMDD-your-post-slug.tex`
2. Convert LaTeX posts to Quarto posts:

```
python tools/convert_latex_posts.py
```

3. Preview locally:

```
quarto preview
```

The converter supports metadata in `%`-commented YAML at the top of each `.tex`
file and maps `\begin{sidework}...\end{sidework}` to Quarto margin blocks.

## Publish / update website

This repo is a Quarto website. Source files live on `main`.

- Local preview: run `quarto preview`
- If you author posts in LaTeX, run `python tools/convert_latex_posts.py` first
- Publishing: push to `main` and GitHub Actions will render + deploy to the `gh-pages` branch

In other words, you generally should **not** manually commit rendered output in `docs/` on `main`.

```
git add .
git commit -m "your message"
git push
```

If you need to publish manually (rare), you can run:

```
quarto publish gh-pages
```

