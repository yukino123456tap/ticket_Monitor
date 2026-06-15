"""
B站会员购票量查询 & 实时监控
用法:
  python main.py <项目ID>            一次性查询
  python main.py <项目ID> -w         实时监控（默认 30s）
  python main.py <项目ID> -w -i 10   每 10s 刷新一次
"""

import sys
import os
import time
import argparse
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://show.bilibili.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://show.bilibili.com/",
    "Cookie": f"SESSDATA={os.getenv('BILI_SESSDATA','')}; bili_jct={os.getenv('BILI_BILI_JCT','')}",
}

# ---------- 核心 API ----------

def get_project(project_id: int) -> dict | None:
    """获取项目详情"""
    url = f"{BASE_URL}/api/ticket/project/get"
    try:
        resp = httpx.get(url, params={"id": project_id}, headers=HEADERS, timeout=15)
        data = resp.json()
        if data.get("errno") != 0:
            return None
        return data["data"]
    except Exception:
        return None


def extract_ticket_snapshot(data: dict) -> dict:
    """
    从 API 返回中抽取出「场次→票档→关键字段」的快照，
    用于变更检测。结构：
      { (screen_name, ticket_id): { "desc", "price", "stock", "total", "is_sold", "buy_limit" } }
    """
    snapshot = {}
    screens = data.get("screen_list") or []
    if not screens or isinstance(screens[0], int):
        return snapshot

    for screen in screens:
        screen_name = screen.get("name", "?")
        for t in screen.get("ticket_list") or []:
            key = (screen_name, t.get("id", "?"))
            snapshot[key] = {
                "desc":       t.get("desc", "?"),
                "price":      t.get("price", 0),
                "stock":      t.get("stock"),
                "total":      t.get("total"),
                "is_sold":    t.get("is_sold_out", False) or t.get("sale_status") == 2,
                "buy_limit":  t.get("buy_limit", ""),
            }
    return snapshot


# ---------- 渲染 ----------

def render_output(data: dict, project_id: int, last_update: str,
                  prev_snapshot: dict | None = None, diffs: set | None = None):
    """
    构建终端输出字符串。
    diffs: 本次有变化的 ticket key 集合，用于高亮。
    """
    lines = []
    name = data.get("name", "未知")
    city = data.get("city", "未知")
    venue = data.get("venue", "未知")
    status = data.get("status", "")
    status_map = {"preselling": "预售中", "onsale": "在售", "offsale": "已下架", "ended": "已结束"}
    status_text = status_map.get(status, status)

    lines.append(f"\033[2J\033[H")  # 清屏 + 光标归位
    lines.append("=" * 56)
    lines.append(f"  🎫 {name}")
    lines.append(f"  状态: {status_text} | {city} | {venue}  |  刷新: {last_update}")
    lines.append("=" * 56)

    screens = data.get("screen_list") or []
    if not screens:
        lines.append("  暂无场次信息")
        return "\n".join(lines)

    if screens and isinstance(screens[0], int):
        lines.append("  ⚠ API 仅返回场次 ID，需确保 Cookie 有效")
        return "\n".join(lines)

    diffs = diffs or set()

    for screen in screens:
        screen_name = screen.get("name", "未命名字段")
        lines.append(f"\n  📅 {screen_name}")

        tickets = screen.get("ticket_list") or []
        if not tickets:
            lines.append("    暂无票档")
            continue

        for t in tickets:
            ticket_id = t.get("id", "?")
            key = (screen_name, ticket_id)
            desc = t.get("desc", "?")
            price = t.get("price", 0)
            is_sold = t.get("is_sold_out", False) or t.get("sale_status") == 2
            stock = t.get("stock")
            total = t.get("total")
            buy_limit = t.get("buy_limit", "")

            status_icon = "❌ 售罄" if is_sold else "✅ 有票"
            price_str = f"¥{price/100:.0f}" if price else "?"
            extra = ""
            if stock is not None:
                extra += f" | 剩余: {stock}"
            if total is not None:
                extra += f"/{total}"
            if buy_limit:
                extra += f" | 限购: {buy_limit}张"

            line = f"    [{ticket_id}] {status_icon} | {price_str} | {desc}{extra}"

            # 变更高亮
            if key in diffs:
                # 如果是售罄→有票，用绿色；有票→售罄，用红色；库存变化用黄色
                prev = prev_snapshot.get(key, {}) if prev_snapshot else {}
                prev_sold = prev.get("is_sold", None)
                prev_stock = prev.get("stock")

                if prev_sold is True and not is_sold:
                    line += "  \033[1;32m⬆ 已补票！\033[0m"
                elif prev_sold is False and is_sold:
                    line += "  \033[1;31m⬇ 已售罄\033[0m"
                elif prev_stock is not None and stock is not None and prev_stock != stock:
                    delta = stock - prev_stock
                    sign = "+" if delta > 0 else ""
                    color = "32" if delta > 0 else "31"
                    line += f"  \033[1;{color}m({sign}{delta})\033[0m"

            lines.append(line)

    lines.append("")
    lines.append("=" * 56)
    lines.append(f"  详情页: https://show.bilibili.com/platform/detail.html?id={project_id}")
    lines.append(f"  按 Ctrl+C 停止监控")
    lines.append("=" * 56)
    return "\n".join(lines)


# ---------- 监控循环 ----------

def watch(project_id: int, interval: int):
    """持续监控票量"""
    prev_snapshot: dict | None = None
    first_run = True

    print("\033[2J\033[H", end="")  # 清屏
    print("  正在连接 B站会员购...")

    while True:
        data = get_project(project_id)
        now = time.strftime("%H:%M:%S")

        if not data:
            # API 失败不退出，打印提示后重试
            print(f"\033[2J\033[H  [{now}] API 请求失败，{interval}s 后重试...")
            time.sleep(interval)
            continue

        current = extract_ticket_snapshot(data)
        diffs: set = set()

        if prev_snapshot is not None:
            # 找出所有变更的票档
            all_keys = set(prev_snapshot.keys()) | set(current.keys())
            for k in all_keys:
                old = prev_snapshot.get(k, {})
                new = current.get(k, {})
                if (
                    old.get("is_sold") != new.get("is_sold") or
                    old.get("stock") != new.get("stock") or
                    old.get("total") != new.get("total")
                ):
                    diffs.add(k)

        # 只在首次或有变化时全量刷新（减少闪烁）
        output = render_output(data, project_id, now, prev_snapshot, diffs)
        sys.stdout.write(output)
        sys.stdout.flush()

        prev_snapshot = current
        first_run = False

        time.sleep(interval)


# ---------- 入口 ----------

def main():
    parser = argparse.ArgumentParser(
        description="B站会员购票量查询 & 实时监控",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py 72743              一次性查询
  python main.py 72743 -w           实时监控（30s 间隔）
  python main.py 72743 -w -i 10     实时监控（10s 间隔）
        """,
    )
    parser.add_argument("project_id", nargs="?", help="项目 ID（从详情页 URL 获取）")
    parser.add_argument("-w", "--watch", action="store_true", help="持续监控模式")
    parser.add_argument("-i", "--interval", type=int, default=30,
                        help="监控间隔（秒），默认 30，最小 5")

    args = parser.parse_args()

    pid = args.project_id
    if not pid:
        pid = input("请输入项目ID: ").strip()
    if not pid.isdigit():
        print("项目ID 必须是数字")
        sys.exit(1)

    project_id = int(pid)
    interval = max(5, args.interval)

    if args.watch:
        print(f"🔍 开始监控项目 {project_id}，每 {interval}s 刷新一次...")
        try:
            watch(project_id, interval)
        except KeyboardInterrupt:
            print(f"\n👋 已停止监控")
    else:
        # 一次性模式，复用渲染（无 diff）
        data = get_project(project_id)
        if not data:
            print("获取项目信息失败，请检查项目 ID 或 Cookie")
            return
        now = time.strftime("%H:%M:%S")
        output = render_output(data, project_id, now)
        # 去掉清屏控制符，适合一次性输出
        output = output.replace("\033[2J\033[H", "")
        print(output)


if __name__ == "__main__":
    main()
