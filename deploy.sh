#!/usr/bin/env bash
# Jekyll GitHub Pages 一键部署脚本
# 用法：在仓库根目录执行 `./deploy.sh`

set -e

# ===== 基本设置 =====
BRANCH="main"
REMOTE_NAME="origin"

# ===== 环境检查 =====
if [ ! -f "_config.yml" ]; then
  echo "❌ 未找到 _config.yml，这看起来不像一个 Jekyll 项目目录。"
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "🔧 初始化 Git 仓库..."
  git init
fi

# ===== 依赖（可选）=====
if [ -f "Gemfile" ]; then
  echo "📦 发现 Gemfile，安装/更新 Bundler 依赖（本地 vendor/bundle）..."
  bundle config set --local path 'vendor/bundle'
  bundle install
fi

# ===== 本地构建检查（不推 _site，只做 sanity check）=====
if command -v bundle >/dev/null 2>&1; then
  echo "🏗️  使用 Bundler 构建（生产环境）..."
  JEKYLL_ENV=production bundle exec jekyll build
else
  echo "🏗️  未检测到 Bundler，尝试直接 jekyll 构建..."
  JEKYLL_ENV=production jekyll build
fi
echo "✅ 本地构建通过，输出目录：_site/（不会推送）"

# ===== Git 提交 & 推送 =====
echo "📝 添加并提交变更..."
git add -A

# 若无变更则退出
if git diff --cached --quiet; then
  echo "ℹ️  没有需要提交的变更。"
else
  git commit -m "Deploy site: $(date '+%Y-%m-%d %H:%M:%S')"
fi

# 切到 main 分支
git branch -M "$BRANCH"

# 检查远程，若没有则给出引导
if ! git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  echo "❗ 未检测到远程 $REMOTE_NAME，请先设置："
  echo "   git remote add origin https://github.com/<USER>/<USER>.github.io.git"
  echo "   或（推荐 SSH） git remote add origin git@github.com:<USER>/<USER>.github.io.git"
  exit 1
fi

echo "🚀 推送到 $REMOTE_NAME/$BRANCH ..."
git push -u "$REMOTE_NAME" "$BRANCH"

echo "🎉 完成！几分钟后访问你的站点： https://$(basename -s .git \"$(git remote get-url $REMOTE_NAME)\")"
