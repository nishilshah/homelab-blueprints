#!/usr/bin/env bash
# ==============================================================================
# Homelab Blueprint Pre-Commit Security & Secrets Scanner
# Ensures no credentials, API keys, passwords, or personal secrets are committed.
# ==============================================================================

set -euo pipefail

echo "🔍 Running Secrets & Credential Sanitization Check..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ERRORS=0

# High-risk patterns
PATTERNS=(
    "NiPr25Nov"
    "NishilTrue"
    "Van@604"
    "Miami@4321"
    "Maunil@143"
    "nishilshah140692"
    "nishilshah_140692"
    "eyJ0eXAiOiJKV1Qi"
    "607a18fc539e5db2c9dbf5deff427062672dddbd"
    "8990389671:AAG"
    "8957095765:AAF"
    "8692774416:AAG"
    "8619272140:AAH"
    "459682a7019947938c2ab8651ca70ab4"
    "71a1d31571a2400786c075585bcb5199"
    "40923b7b120a46449233646274e26f75"
    "2417f89172994ef890cf2d5ba7a401de"
    "dfca64bed91a2954596aeb1eb003df3a"
    "gXt5IKH81LHD8IaB2tkjB4dKtzfMkG23"
    "U5YYi0LLY"
    "1240579489"
    "HQ4K9FWK6CAD"
    "673026788"
    "3288134"
)

for pattern in "${PATTERNS[@]}"; do
    if grep -rnF --exclude-dir=".git" --exclude="sanitize-check.sh" "$pattern" "$REPO_ROOT" > /dev/null 2>&1; then
        echo "❌ SECURITY ALERT: Found sensitive credential or real identifier matching pattern: $pattern"
        grep -rnF --exclude-dir=".git" --exclude="sanitize-check.sh" "$pattern" "$REPO_ROOT"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check for private key headers
if grep -rnE --exclude-dir=".git" "-----BEGIN (RSA|OPENSSH|EC|DSA|PRIVATE) KEY-----" "$REPO_ROOT" > /dev/null 2>&1; then
    echo "❌ SECURITY ALERT: Found private key header!"
    ERRORS=$((ERRORS + 1))
fi

if [ "$ERRORS" -gt 0 ]; then
    echo "🚨 Security Check FAILED. Aborting commit to prevent credential leak."
    exit 1
else
    echo "✅ Clean! No private credentials or secrets found."
    exit 0
fi
