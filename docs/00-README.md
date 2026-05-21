# Personal Podcast Monitoring Agent — Build Spec

**Owner:** Hamid (hamid@lendhub.co.uk)
**Spec written:** 2026-05-21
**Intended builder:** Claude Code agent

---

## What this is

A personal AI agent that runs once a day on Anthropic-managed cloud infrastructure, checks a hand-curated list of podcasts in a Notion database, fetches transcripts for any new episodes from YouTube, summarizes them through Claude using a personal interest profile, and delivers a structured daily briefing to Notion, Slack, and email.

Inspired by Gavin Baker's "single most useful agent" described on Invest Like the Best (May 2026): a podcast briefing agent that surfaces the points he'd find interesting from 6+ hours of daily content. This build replicates and personalizes that pattern.

---

## Design principles

1. **Free where free is robust enough.** No paid transcript vendor. Uses RSS (feedparser) for episode discovery and YouTube auto-captions (youtube-transcript-api) for transcripts. Total external cost is Claude tokens + Managed Agent runtime, target sub-$10/month.
2. **Notion as source of truth.** All podcast lists, interest profile, and briefing output live in Notion. Hamid maintains the list by hand; the agent reads/writes only.
3. **Claude reasoning over brittle code.** Title-mismatch between RSS and YouTube, speaker disambiguation, "is this episode really new" judgement — all handled by Claude in-prompt, not by string-matching logic.
4. **Memory and feedback loop.** Agent maintains memory of seen episodes and what Hamid flagged as useful. Over weeks the briefing tunes to what he actually reads.
5. **Multi-channel delivery.** Notion (full briefing, searchable), Slack (short ping), email (fallback).

---

## File map for this spec

| File | Purpose |
|---|---|
| `00-README.md` | This file — overview and reading order |
| `01-architecture.md` | End-to-end system design and data flow |
| `02-notion-schemas.md` | Exact Notion database schemas to create |
| `03-managed-agent-config.md` | The Anthropic Managed Agent definition (model, tools, MCP, memory) |
| `04-system-prompt.md` | The agent's system prompt with interest profile template |
| `05-daily-run-prompt.md` | The user-turn prompt sent at each scheduled run |
| `06-code-modules.md` | Python helpers the agent's bash tool will execute (feedparser, youtube fetch) |
| `07-deployment.md` | Step-by-step deployment: API keys, agent creation, scheduling |
| `08-verification.md` | First-run checklist and troubleshooting |
| `09-future-extensions.md` | What to add once the core works |

Read in order. Each file is self-contained enough to act on, but cross-references the others.

---

## Reference: API and feature versions used

This spec targets the **Claude Managed Agents** public beta as of May 2026.

- Beta header: `managed-agents-2026-04-01`
- Built-in tool bundle: `agent_toolset_20260401` (bash, read, write, edit, glob, grep, web_search, web_fetch)
- Model: `claude-sonnet-4-6` (recommended) or `claude-opus-4-6` (if cost is no object)
- Memory: public beta, no extra header
- Outcomes: public beta, no extra header
- Dreaming: research preview, requires `dreaming-2026-04-21` header and access request (optional for v1)

If newer versions exist when building, prefer the latest stable.

---

## Alternative runtime: Claude Code Routines

There is a simpler alternative primitive worth knowing: **Claude Code Routines**. These are saved Claude Code configurations (prompt + repos + connectors) that run on Anthropic-managed cloud on a recurring schedule (min interval 1 hour, supports cron). If the builder finds the Managed Agents API too heavy for a personal tool, Routines may be a faster path with the same outcome.

Decision criterion: if Hamid wants to evolve this agent into something with custom memory schemas, multi-agent orchestration, or programmatic control from other apps, use **Managed Agents**. If he just wants "this prompt runs every morning," use **Routines**. This spec targets Managed Agents for future-proofing but the prompt/architecture is portable to either.

---

## Sources

- [Claude Managed Agents overview](https://platform.claude.com/docs/en/managed-agents/overview)
- [New in Claude Managed Agents: dreaming, outcomes, multiagent](https://claude.com/blog/new-in-claude-managed-agents)
- [Run prompts on a schedule (Claude Code Routines)](https://code.claude.com/docs/en/scheduled-tasks)
- [MCP connector docs](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector)
- [youtube-transcript-api on PyPI](https://pypi.org/project/youtube-transcript-api/)
