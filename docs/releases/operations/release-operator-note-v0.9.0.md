# Chronicle Stack v0.9.0 Release Operator Note

The current assistant environment can prepare repository files and GitHub issues but does not expose a direct Git tag or GitHub Release creation action for this repository.

Therefore, final release execution requires a maintainer shell with `git` and `gh` access.

Use:

```bash
git tag -a v0.9.0 -m "Chronicle Stack v0.9.0"
git push origin v0.9.0

gh release create v0.9.0 \
  --repo zyx-corporation/chronicle-stack \
  --title "Chronicle Stack v0.9.0" \
  --notes-file ../notes/release-notes-v0.9.0.md
```

After release creation, run installer smoke and post the result back to the release issue.
