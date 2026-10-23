#!/usr/bin/env bash
# Vercel Ignored Build Step, run through vercel.json's "ignoreCommand".
# Exit 0 skips the build and exit 1 builds; any other code fails the
# deployment, so this script only ever exits 0 or 1 and builds when unsure.
#
# The base is the last commit Vercel deployed (VERCEL_GIT_PREVIOUS_SHA), not
# HEAD^: Vercel builds only the newest commit of a push, so a HEAD^ diff would
# skip source changes made by an earlier commit in the same push.
#
# git diff needs .git in the build, so never list .git in .vercelignore.

base="${VERCEL_GIT_PREVIOUS_SHA:-}"
if [ -z "$base" ] || ! git cat-file -e "${base}^{commit}" 2>/dev/null; then
  echo "No previous deployment in this clone (VERCEL_GIT_PREVIOUS_SHA='${base}'); building."
  exit 1
fi

# Paths that never reach the deployed app. Anything not listed here builds.
if git diff --quiet "$base" HEAD -- . \
  ':(exclude)docs' \
  ':(exclude).github' \
  ':(exclude).impeccable' \
  ':(exclude)apps/api' \
  ':(exclude)apps/web/e2e' \
  ':(exclude)apps/web/tests' \
  ':(exclude)content/drafts' \
  ':(exclude)Dockerfile.backend' \
  ':(exclude)railway.json' \
  ':(exclude).pre-commit-config.yaml' \
  ':(exclude,glob)*.md'; then
  echo "Only docs, tests or CI files changed since ${base:0:7}; skipping the build."
  exit 0
fi

echo "Deployable files changed since ${base:0:7}; building."
exit 1
