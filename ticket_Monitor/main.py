"""
B站会员购票量查询
用法: python main.py <项目ID>
示例: python main.py 12345
"""

import sys
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://show.bilibili.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://show.bilibili.com/",
    "Cookie": f"SESSDATA={os.getenv('BILI_SESSDATA','')}; bili_jct={os.getenv('BILI_BILI_JCT','')}",
}


def get_project(project_id: int) -> dict | None:
    """获取项目详情"""
    url = f"{BASE_URL}/api/ticket/project/get"
    try:
        resp = httpx.get(url, params={"id": project_id}, headers=HEADERS, timeout=15)
        data = resp.json()
        if data.get("errno") != 0:
            print(f"API 错误: {data.get('msg', '未知错误')}")
            return None
        return data["data"]
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def show_tickets(project_id: int):
    """查询并展示票量"""
    data = get_project(project_id)
    if not data:
        return

    # 基本信息
    name = data.get("name", "未知")
    city = data.get("city", "未知")
    venue = data.get("venue", "未知")
    status = data.get("status", "")
    status_map = {"preselling": "预售中", "onsale": "在售", "offsale": "已下架", "ended": "已结束"}
    status_text = status_map.get(status, status)

    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"  状态: {status_text} | {city} | {venue}")
    print(f"{'='*50}")

    # 场次 & 票档
    screens = data.get("screen_list") or []
    if not screens:
        print("  暂无场次信息")
        return

    # 处理 screen_list 是 int 列表的情况（仅场次ID）
    if screens and isinstance(screens[0], int):
        print("  API 返回的场次数据不完整（仅 ID），需要登录后重试")
        return

    for screen in screens:
        screen_name = screen.get("name", "未命名字段")
        print(f"\n  📅 {screen_name}")

        tickets = screen.get("ticket_list") or []
        if not tickets:
            print("    暂无票档")
            continue

        for t in tickets:
            ticket_id = t.get("id", "?")
            desc = t.get("desc", "?")
            price = t.get("price", 0)
            # 售罄判断：is_sold_out 或 sale_status==2
            is_sold = t.get("is_sold_out", False) or t.get("sale_status") == 2

            # 补充字段（部分API有）
            stock = t.get("stock")  # 剩余量
            total = t.get("total")  # 总量
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

            print(f"    [{ticket_id}] {status_icon} | {price_str} | {desc}{extra}")

    print(f"\n{'='*50}")
    print(f"  详情页: https://show.bilibili.com/platform/detail.html?id={project_id}")
    print()


def main():
    if len(sys.argv) < 2:
        print("用法: python main.py <项目ID>")
        print("示例: python main.py 12345")
        print()
        pid = input("请输入项目ID: ").strip()
    else:
        pid = sys.argv[1]

    if not pid.isdigit():
        print("项目ID 必须是数字")
        sys.exit(1)

    show_tickets(int(pid))


if __name__ == "__main__":
    main()
