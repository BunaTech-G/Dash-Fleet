#!/usr/bin/env bash
set -euo pipefail

# Usage: create_org.sh <ACTION_TOKEN> [ORG_NAME]
# Environment: optionally set HOST (default http://localhost:5000)

HOST=${HOST:-http://localhost:5000}
TOKEN=${1:-}
NAME=${2:-"MyOrganization"}

if [ -z "$TOKEN" ]; then
  echo "Usage: $0 <ACTION_TOKEN> [ORG_NAME]"
  exit 2
fi

resp=$(curl -s -w "\n%{http_code}" -X POST "$HOST/api/orgs" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"name\": \"$NAME\"}")

body=$(echo "$resp" | sed '$d')
code=$(echo "$resp" | tail -n1)

if [ "$code" -ne 200 ]; then
  echo "Request failed with status $code"
  echo "$body"
  exit 3
fi

echo "Server response:"
echo "$body" | sed -n '1,200p'

if command -v jq >/dev/null 2>&1; then
  echo
  echo "org_id: $(echo "$body" | jq -r '.id')"
  echo "api_key: $(echo "$body" | jq -r '.api_key')"
else
  api_key=$(printf "%s" "$body" | python -c "import sys,json; print(json.load(sys.stdin).get('api_key'))")
  org_id=$(printf "%s" "$body" | python -c "import sys,json; print(json.load(sys.stdin).get('id'))")
  echo
  echo "org_id: $org_id"
  echo "api_key: $api_key"
fi
