#!/bin/bash
# Trigger a manual podcast briefing run via the Managed Agents API.
# Usage: ./scripts/trigger_run.sh
#
# Required env vars:
#   ANTHROPIC_API_KEY
#   NOTION_TOKEN
#
# The agent will read Notion, fetch RSS, summarize, and write the briefing.

set -euo pipefail

AGENT_ID="agent_01WJQzuPhtF7m3gSJFFicboY"
ENV_ID="env_01NqkFM2wqQMYZoJwS6fpSZn"
BETA="managed-agents-2026-04-01"
TODAY=$(TZ="Europe/London" date +%Y-%m-%d)

echo "=== Podcast Briefing Run: $TODAY ==="

# Create session
echo "Creating session..."
SESSION_ID=$(curl -sfS "https://api.anthropic.com/v1/sessions" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: $BETA" \
  -H "content-type: application/json" \
  -d "{\"agent\": \"$AGENT_ID\", \"environment_id\": \"$ENV_ID\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Session: $SESSION_ID"

# Send the daily run prompt
echo "Sending daily run prompt..."
PROMPT=$(cat <<PROMPT_EOF
Run your daily podcast briefing for $TODAY (timezone: Europe/London).

FIRST: set up environment:
\`\`\`bash
export NOTION_TOKEN="$NOTION_TOKEN"
export NOTION_PODCASTS_DB_ID="27d43c5f-e417-4b63-ac76-970108d6440a"
export NOTION_BRIEFINGS_DB_ID="9efebf0f-01ba-459c-9709-ca80e1ac23af"
export NOTION_INTEREST_PROFILE_PAGE_ID="3672897b-8e36-812a-8f1f-e186d1adedf2"
\`\`\`

Execute your daily routine end-to-end. Skip email.
PROMPT_EOF
)

python3 -c "
import json, requests, os
resp = requests.post(
    f'https://api.anthropic.com/v1/sessions/$SESSION_ID/events',
    headers={
        'x-api-key': os.environ['ANTHROPIC_API_KEY'],
        'anthropic-version': '2023-06-01',
        'anthropic-beta': '$BETA',
        'content-type': 'application/json',
    },
    json={'events': [{'type': 'user.message', 'content': [{'type': 'text', 'text': '''$PROMPT'''}]}]},
)
print(f'Sent: {resp.status_code}')
"

echo ""
echo "Session running. Monitor at:"
echo "  curl -s 'https://api.anthropic.com/v1/sessions/$SESSION_ID' \\"
echo "    -H 'x-api-key: \$ANTHROPIC_API_KEY' \\"
echo "    -H 'anthropic-version: 2023-06-01' \\"
echo "    -H 'anthropic-beta: $BETA' | python3 -m json.tool"
