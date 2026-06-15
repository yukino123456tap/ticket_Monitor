# 🎫 B站会员购票量查询

输入项目 ID，一键查询 B站会员购活动的票档和库存。

## 快速开始

```bash
# 1. 安装
pip install -r requirements.txt

# 2. 配置 Cookie
cp .env.example .env
# 编辑 .env，填入 BILI_SESSDATA 和 BILI_BILI_JCT

# 3. 运行
python main.py 12345
```

## 获取 Cookie

1. 浏览器打开 [show.bilibili.com](https://show.bilibili.com) 并登录
2. `F12` → `Application` → `Cookies` → 复制 `SESSDATA` 和 `bili_jct`

## 获取项目 ID

在 B站会员购活动详情页 URL 中：
`https://show.bilibili.com/platform/detail.html?id=72743`
→ 项目 ID 就是 `72743`

## 示例输出

```
==================================================
  2024 BW 漫展
  状态: 在售 | 上海 | 国家会展中心
==================================================

  📅 7月12日 周五
    [1001] ✅ 有票 | ¥128 | 早鸟票 | 剩余: 320/500 | 限购: 2张
    [1002] ❌ 售罄 | ¥168 | 标准票 | 剩余: 0/1000

==================================================
  详情页: https://show.bilibili.com/platform/detail.html?id=72743
```

## License

MIT
