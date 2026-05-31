# Security Policy

## Supported Versions

This project is pre-1.0. Security fixes are applied to the current `main` branch.

## Reporting a Vulnerability

Do not open a public issue for secrets, data exposure, or SQL execution bypasses.

Report privately to the repository owner with:

- A short description of the issue.
- Reproduction steps or a proof of concept.
- Any affected commit, branch, or deployment details.

## Data and Secrets

- Do not commit `.env` files, credentials, private datasets, SQLite database dumps, model checkpoints, or adapter artifacts.
- Rotate any credential that may have been committed or exposed in logs.
- Run `sh scripts/scan_secrets.sh` before publishing or opening a pull request.

## SQL Execution Scope

SchemaSage is designed for demo SQLite data. Before connecting it to non-demo data, add authentication, request limits, audit logging, network controls, and data-access review.
