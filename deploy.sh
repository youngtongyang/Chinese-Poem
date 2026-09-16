#!/usr/bin/env bash
# 《望庐山瀑布》页面部署脚本
# 把 /root/code/poem-video/ 发布到 nginx 站点目录 /var/www/poem/
# 用法: sudo bash deploy.sh
set -euo pipefail

SRC="/root/code/poem-video"
DEST="/var/www/poem"

echo "▶ 发布 $SRC → $DEST"
mkdir -p "$DEST"

# 只发布页面与素材，不发布脚本/预览图/README
cp "$SRC/index.html" "$DEST/"
cp -r "$SRC/assets" "$DEST/"

# favicon
if [ -f "$SRC/favicon.png" ]; then
  cp "$SRC/favicon.png" "$DEST/"
fi

# 权限：nginx worker 需要可读
chown -R nginx:nginx "$DEST"
find "$DEST" -type d -exec chmod 755 {} \;
find "$DEST" -type f -exec chmod 644 {} \;

echo "▶ 校验 nginx 配置"
nginx -t

echo "▶ 重载 nginx"
nginx -s reload

echo "▶ 验证"
for p in "/poem/" "/poem/index.html" "/poem/assets/main2.jpeg" "/poem/assets/portrait.jpeg"; do
  printf "  %-28s -> HTTP %s\n" "$p" "$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "http://127.0.0.1$p")"
done

echo "✓ 部署完成"
