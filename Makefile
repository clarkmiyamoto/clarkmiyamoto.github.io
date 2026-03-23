.PHONY: latex-posts preview render

latex-posts:
	python tools/convert_latex_posts.py

preview: latex-posts
	quarto preview

render: latex-posts
	quarto render
