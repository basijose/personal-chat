# Deployment Flow

Personal Chat uses two Git branches to separate validation from release:

- `testing`: integration branch for verification, demos, and pre-release checks.
- `production`: release branch that should represent the deployed version.

## Recommended flow

1. Develop changes in a feature branch.
2. Merge or push into `testing`.
3. GitHub Actions runs backend tests, frontend lint, frontend tests, and frontend build.
4. After validation, open a pull request from `testing` into `production`.
5. Merge only when the checks are green and the change is approved.

## GitHub Actions

The repository includes a CI workflow at `.github/workflows/ci.yml`.

It runs on pushes and pull requests targeting `testing` and `production` and keeps both environments aligned with the same checks.

## Environment naming

The workflow marks each run with the GitHub Actions environment matching the branch:

- pushes to `testing` use the `testing` environment
- pushes to `production` use the `production` environment

That makes it easy to add environment-specific secrets or approvals later without changing the application code.

## Production hardening

When you're ready, the next step is to add branch protection rules on `production` so that:

- direct pushes are blocked
- a pull request is required
- the `backend` and `frontend` checks must pass
