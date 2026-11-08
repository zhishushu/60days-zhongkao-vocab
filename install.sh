#!/usr/bin/env bash
# 60天搞定中考词汇 · 一键安装到 AI 助手的 skills 目录
#
# 用法：
#   ./install.sh                 # 自动判断：有 Hermes 装 Hermes，否则装 Claude Code
#   ./install.sh --hermes        # 装到 $HERMES_HOME/skills/productivity/60days-zhongkao-vocab
#   ./install.sh --claude        # 装到 ~/.claude/skills/60days-zhongkao-vocab
#   ./install.sh --target DIR    # 装到指定目录（任何支持 SKILL.md 的助手都行）
#
set -euo pipefail

NAME="60days-zhongkao-vocab"
CAT="productivity"
MODE="auto"
TARGET=""

usage() {
  sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
}

while [ $# -gt 0 ]; do
  case "$1" in
    --hermes) MODE="hermes" ;;
    --claude) MODE="claude" ;;
    --target) TARGET="${2:-}"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数：$1"; usage; exit 1 ;;
  esac
  shift
done

SRC="$(cd "$(dirname "$0")" && pwd)"
if [ ! -f "$SRC/SKILL.md" ]; then
  echo "✗ 这个脚本要在仓库根目录里运行（找不到 SKILL.md）" >&2
  exit 1
fi

if [ -z "$TARGET" ]; then
  case "$MODE" in
    hermes)
      TARGET="${HERMES_HOME:-$HOME/.hermes}/skills/$CAT/$NAME" ;;
    claude)
      TARGET="$HOME/.claude/skills/$NAME" ;;
    auto)
      if [ -n "${HERMES_HOME:-}" ]; then
        TARGET="$HERMES_HOME/skills/$CAT/$NAME"
      elif [ -d "$HOME/.hermes" ]; then
        TARGET="$HOME/.hermes/skills/$CAT/$NAME"
      else
        TARGET="$HOME/.claude/skills/$NAME"
      fi ;;
  esac
fi

echo "→ 安装到：$TARGET"
mkdir -p "$(dirname "$TARGET")"
rm -rf "$TARGET"
mkdir -p "$TARGET"
( cd "$SRC" && tar --exclude='./.git' -cf - . ) | ( cd "$TARGET" && tar -xf - )

echo
echo "✅ 安装完成"
echo "   skill 目录：$TARGET"
echo
echo "下一步（二选一）："
echo "  1) 在 AI 助手里说：「用 60days-zhongkao-vocab 帮我做词汇训练页」"
echo "  2) 先本地试跑："
echo "     python3 \"$TARGET/scripts/generate.py\" \"$TARGET/assets/sample-wordlist.json\" 示例.html"
echo
echo "卸载：rm -rf \"$TARGET\""
