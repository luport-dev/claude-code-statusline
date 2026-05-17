#!/bin/bash
INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // ""' 2>/dev/null)
BRANCH=$(git -C "${CWD:-.}" branch --show-current 2>/dev/null)
WORKTREE=$(echo "$INPUT" | jq -r '.worktree.name // ""' 2>/dev/null)
THINKING=$(jq -r '.alwaysThinkingEnabled // false' "$HOME/.claude/settings.json" 2>/dev/null)
ESC=$'\e'
echo "$INPUT" | jq -r --arg branch "$BRANCH" --arg worktree "$WORKTREE" --arg thinking "$THINKING" --arg e "$ESC" '
  def thinking_on: ($thinking == "true");
  def reset: $e+"[0m";
  def dim: $e+"[2m";
  def color(v; warn; crit): if v >= crit then $e+"[31m" elif v >= warn then $e+"[33m" else $e+"[32m" end;
  def model_color(m): if (m|ascii_downcase|contains("opus")) then $e+"[38;2;255;215;0m" elif (m|ascii_downcase|contains("sonnet")) then $e+"[38;2;100;180;255m" elif (m|ascii_downcase|contains("haiku")) then $e+"[38;5;255m" else $e+"[37m" end;
  def effort_color(e2): if e2 == "xhigh" then $e+"[31m" elif e2 == "high" then $e+"[38;5;208m" elif e2 == "medium" then $e+"[33m" else $e+"[32m" end;
  def dim_gray: $e+"[2;37m";
  def thinking_color(t): if t then $e+"[38;2;80;220;200m" else $e+"[2;37m" end;
  def lbl(l; c): c+l+":"+reset;
  def sep: " "+dim+"|"+reset+" ";
  def is_haiku: (.model.display_name // "" | ascii_downcase | contains("haiku"));
  def effort_display: if is_haiku then (dim_gray + "n/a" + reset) else (effort_color(.effort.level) + .effort.level + reset) end;
  def thinking_display: if thinking_on then (thinking_color(true) + "thinking:on" + reset) else (dim_gray + "thinking:off" + reset) end;
  (
    [
      (model_color(.model.display_name) + .model.display_name + reset),
      sep,
      ((if is_haiku then dim_gray else effort_color(.effort.level) end) + "effort:" + reset + effort_display),
      sep,
      thinking_display,
      sep,
      (lbl("ctx"; color((.context_window.used_percentage // 0); 70; 90)) + color((.context_window.used_percentage // 0); 70; 90) + ((.context_window.used_percentage // 0)|floor|tostring) + "%" + reset),
      sep,
      (lbl("5h"; color((.rate_limits.five_hour.used_percentage // 0); 70; 90)) + color((.rate_limits.five_hour.used_percentage // 0); 70; 90) + ((.rate_limits.five_hour.used_percentage // 0)|floor|tostring) + "%" + reset),
      sep,
      (lbl("7d"; color((.rate_limits.seven_day.used_percentage // 0); 50; 80)) + color((.rate_limits.seven_day.used_percentage // 0); 50; 80) + ((.rate_limits.seven_day.used_percentage // 0)|floor|tostring) + "%" + reset)
    ] | join("")
  ) + "\n" + (
    [
      (($e+"[38;5;130m")+"dir:"+reset+($e+"[38;5;172m") + (.cwd // "?") + reset),
      sep, (($e+"[38;5;130m")+"branch:"+reset+($e+"[38;5;172m") + (if $branch != "" then $branch else "-" end) + reset),
      sep, (($e+"[38;5;130m")+"worktree:"+reset+($e+"[38;5;172m") + (if $worktree != "" then $worktree else "-" end) + reset)
    ] | join("")
  )
' 2>/dev/null || echo "?"
