# 🎫 B站会员购票量查询 & 实时监控

输入项目 ID，查询 B站会员购活动的票档和库存，支持**实时监控模式**自动刷新票量变化。

## 快速开始

```bash
# 1. 安装
pip install -r requirements.txt

# 2. 配置 Cookie
cp .env.example .env
# 编辑 .env，填入 BILI_SESSDATA 和 BILI_BILI_JCT

# 3. 一次性查询
python main.py 72743

# 4. 实时监控（每 30s 自动刷新）
python main.py 72743 -w

# 5. 自定义刷新间隔（每 10s）
python main.py 72743 -w -i 10
```

## 监控模式特性

- **自动刷新**：终端原地更新，不刷屏
- **变更高亮**：
  - 🟢 **补票** — 售罄→有票，绿色高亮
  - 🔴 **售罄** — 有票→售罄，红色高亮
  - 🟡 **库存变化** — 显示 `+N` 或 `-N`
- 按 `Ctrl+C` 退出监控

## 获取 Cookie

1. 浏览器打开 [show.bilibili.com](https://show.bilibili.com) 并登录
2. `F12` → `Application` → `Cookies` → 复制 `SESSDATA` 和 `bili_jct`

## 获取项目 ID

在 B站会员购活动详情页 URL 中：
`https://show.bilibili.com/platform/detail.html?id=72743`
→ 项目 ID 就是 `72743`

## 用法

```
用法:
  python main.py <项目ID>            一次性查询
  python main.py <项目ID> -w         实时监控（默认 30s）
  python main.py <项目ID> -w -i 10   每 10s 刷新一次
```

## 示例输出

```
==========================================================
  🎫 2024 BW 漫展
  状态: 在售 | 上海 | 国家会展中心  |  刷新: 14:32:05
==========================================================

  📅 7月12日 周五
    [1001] ✅ 有票 | ¥128 | 早鸟票 | 剩余: 320/500 | 限购: 2张
    [1002] ❌ 售罄 | ¥168 | 标准票 | 剩余: 0/1000

==========================================================
  详情页: https://show.bilibili.com/platform/detail.html?id=72743
  按 Ctrl+C 停止监控
```

## License

MIT
