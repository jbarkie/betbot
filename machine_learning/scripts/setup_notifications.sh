#!/bin/bash
# Build the local macOS notifier. Authorization is a separate explicit action.
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP="$PROJECT_ROOT/.local/BetBot Notifier.app"
[ "$(uname -s)" = Darwin ] || { echo "macOS is required" >&2; exit 1; }
mkdir -p "$APP/Contents/MacOS"
cp "$PROJECT_ROOT/machine_learning/scripts/notifications/Info.plist" "$APP/Contents/Info.plist"
xcrun swiftc -module-cache-path "$PROJECT_ROOT/.local/swift-cache" \
    "$PROJECT_ROOT/machine_learning/scripts/notifications/BetBotNotifier.swift" \
    -o "$APP/Contents/MacOS/BetBotNotifier"
codesign --force --sign - --identifier com.betbot.notifier "$APP"
echo "Built $APP"
echo "Request permission: bash machine_learning/scripts/notify_macos.sh --authorize"
