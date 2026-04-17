#!/usr/bin/env bash
branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$branch" = "master" ] || [ "$branch" = "dev" ]; then
    echo "BLOCKED: Direct push to '$branch' is not allowed."
    echo "Create a feature branch from dev and use PR:"
    echo "  git checkout -b {type}/{description} dev"
    echo "  git push origin {type}/{description}"
    echo "  gh pr create --base dev"
    exit 1
fi
