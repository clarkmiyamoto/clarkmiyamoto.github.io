# clarkmiyamoto.github.io

# Locally preview webiste
```
quarto preview
```

# Update Website

Pull latest changes from `_ExternalRepos`
```
git pull --recurse-submodules
```
Use quarto to `/docs`
```
quarto publish gh-pages
```
then finally push to GitHub
```
git add .
git commit -m "stuff"
git push main
```