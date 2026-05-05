# Release Workflow

> **Standard operating procedure for releasing V-Pack Monitor.**
> Shared between OpenCode and Antigravity.

---

## Prerequisites

- All feature branches merged to dev
- No pending PRs marked as blockers

## Step 1: Update Version on dev

```bash
git checkout dev && git pull origin dev
# Update VERSION file: v3.0.0 → v3.1.0
# Update vpack/app.py header: v3.0.0 → v3.1.0
# Add RELEASE_NOTES.md entry for new version
git commit -m "release: vX.Y.Z — update VERSION, release notes"
git push origin dev
```

## Step 2: Create Release Branch from dev

```bash
git checkout -b release/vX.Y.Z dev
git push origin release/vX.Y.Z
```

## Step 3: Create PR to master

```bash
gh pr create --base master --title "Release vX.Y.Z" --body "Release notes from RELEASE_NOTES.md"
```

## Step 4: Wait CI Pass

If "not up to date with base":
```bash
git fetch origin master
git merge origin/master --no-edit
git push origin release/vX.Y.Z
```

## Step 5: Merge with MERGE COMMIT (CRITICAL)

```bash
gh pr merge <N> --merge    # ← MUST be --merge, NEVER --squash
```

## Step 6: Create Git Tag + GitHub Release

```bash
# Read version from VERSION file
VERSION=$(cat VERSION | tr -d 'v')

# Create annotated tag on master
git checkout master && git pull origin master
git tag -a "v${VERSION}" -m "Release v${VERSION}"
git push origin "v${VERSION}"

# Create GitHub release from tag
gh release create "v${VERSION}" \
  --title "v${VERSION} — $(head -1 RELEASE_NOTES.md | sed 's/^# //')" \
  --notes-file RELEASE_NOTES.md
```

## Step 7: Sync dev from master (CRITICAL)

After release merge, dev must receive the merge commit + version bump from master. Without this, dev falls behind master on VERSION/vpack/app.py/RELEASE_NOTES → next release will conflict.

```bash
git checkout dev && git pull origin dev
git merge origin/master --no-edit
git push origin dev
```

**Why**: The `--merge` release PR creates a merge commit on master that dev doesn't have. If dev isn't synced, the next release branch (created from dev) will conflict on VERSION/vpack/app.py/RELEASE_NOTES when Step 4 merges master into it.

## Step 8: Verify

```bash
git checkout dev && git pull origin dev
git checkout master && git pull origin master
git log --oneline -5 master  # Should show merge commit
git tag -l 'v*' | sort -V | tail -3  # Should show new tag
gh release list --limit 3   # Should show new release

# Verify dev ≤ master (no conflicts next release)
git log --oneline dev..master  # Should be empty or only merge commit
```

## ⚠️ ABSOLUTELY NEVER

- ❌ `--squash` for release PR → breaks shared history → permanent conflicts
- ❌ `git rebase` dev onto master → rewrites history
- ❌ `git push --force` master → loses release history
- ❌ Forget to create git tag + GitHub release → no version tracking in GitHub
- ❌ Skip Step 7 (sync dev from master) → next release WILL conflict on VERSION/vpack/app.py/RELEASE_NOTES
