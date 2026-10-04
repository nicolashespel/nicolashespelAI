# Claude Code Configuration for RAG Wiki

## Instructions
You are a disciplined wiki maintainer. Follow the SKILL.md rules strictly.

## Commands

### /wiki-init
Initialize a new wiki vault.

### /wiki-ingest <path>
Ingest a source file and update the wiki.

### /wiki-query <query>
Query the wiki and return a synthesized answer.

### /wiki-lint
Run health checks on the wiki.

### /wiki-log
Show the operation log.

## Rules
1. Never edit files in raw/
2. Always update index.md
3. Always log operations in log.md
4. Cross-reference everything
5. Flag contradictions explicitly
