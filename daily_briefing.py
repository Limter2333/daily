#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日早报系统 - Daily Morning Briefing
======================================
自动获取天气、新闻资讯，并推荐适合做的事情
"""

import requests
import json
import random
from datetime import datetime, timedelta
from typing import Optional
import sys
import os
import io

# 设置标准输出编码为 UTF-8 (解决 Windows 终端编码问题)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ============================================================
# 配置区域 - 可根据需要修改
# ============================================================
CONFIG = {
    # 城市设置（用于天气查询）
    "city": "Beijing",  # 可改为你的城市拼音，如 Shanghai, Guangzhou, Shenzhen

    # 是否使用彩色输出
    "colorful": True,

    # 新闻来源数量限制
    "news_limit": 10,
}


# ============================================================
# ANSI 颜色代码
# ============================================================
class Colors:
    if sys.platform == "win32":
        os.system("")  # 启用 Windows 终端 ANSI 支持

    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    @classmethod
    def disable(cls):
        cls.HEADER = cls.BLUE = cls.CYAN = cls.GREEN = ''
        cls.YELLOW = cls.RED = cls.BOLD = cls.UNDERLINE = cls.END = ''


# ============================================================
# 天气模块
# ============================================================
def fetch_weather(city: str) -> Optional[dict]:
    """从 wttr.in 获取天气信息"""
    try:
        url = f"https://wttr.in/{city}?format=j1&lang=zh"
        headers = {"User-Agent": "DailyBriefing/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"{Colors.YELLOW}⚠ 天气获取失败: {e}{Colors.END}")
        return None


def format_weather(data: dict) -> str:
    """格式化天气信息"""
    if not data:
        return "天气信息暂不可用"

    current = data.get("current_condition", [{}])[0]
    weather_desc = current.get("lang_zh", [{}])
    if weather_desc:
        weather_desc = weather_desc[0].get("value", "未知")
    else:
        weather_desc = current.get("weatherDesc", [{}])[0].get("value", "未知")

    temp = current.get("temp_C", "N/A")
    feels_like = current.get("FeelsLikeC", "N/A")
    humidity = current.get("humidity", "N/A")
    wind_speed = current.get("windspeedKmph", "N/A")
    wind_dir = current.get("winddir16Point", "N/A")
    visibility = current.get("visibility", "N/A")
    uv_index = current.get("uvIndex", "N/A")

    # 获取今日预报
    today_forecast = data.get("weather", [{}])[0]
    max_temp = today_forecast.get("maxtempC", "N/A")
    min_temp = today_forecast.get("mintempC", "N/A")
    sunrise = today_forecast.get("astronomy", [{}])[0].get("sunrise", "N/A")
    sunset = today_forecast.get("astronomy", [{}])[0].get("sunset", "N/A")

    # 获取小时预报
    hourly = today_forecast.get("hourly", [])

    output = []
    output.append(f"🌡️  当前温度: {temp}°C (体感 {feels_like}°C)")
    output.append(f"🌤️  天气状况: {weather_desc}")
    output.append(f"📊  温度范围: {min_temp}°C ~ {max_temp}°C")
    output.append(f"💧 湿度: {humidity}%")
    output.append(f"💨 风速: {wind_speed} km/h ({wind_dir})")
    output.append(f"👁️  能见度: {visibility} km")
    output.append(f"☀️  紫外线指数: {uv_index}")
    output.append(f"🌅 日出: {sunrise} | 🌇 日落: {sunset}")

    # 空气质量建议
    uv_val = int(uv_index) if uv_index != "N/A" else 0
    if uv_val >= 8:
        output.append(f"{Colors.RED}⚠️  紫外线很强，建议做好防晒！{Colors.END}")
    elif uv_val >= 6:
        output.append(f"{Colors.YELLOW}⚠️  紫外线较强，注意防晒{Colors.END}")

    return "\n".join(output)


# ============================================================
# 新闻模块 - 多源获取
# ============================================================
def fetch_news_zhihu() -> list:
    """获取知乎热榜"""
    try:
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=10"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            news = []
            for item in data.get("data", []):
                target = item.get("target", {})
                title = target.get("title", "")
                detail = item.get("detail_text", "")
                if title:
                    news.append({
                        "title": title,
                        "source": "知乎热榜",
                        "heat": detail
                    })
            return news
    except Exception:
        pass
    return []


def fetch_news_36kr() -> list:
    """获取36氪快讯"""
    try:
        url = "https://36kr.com/api/newsflash?per_page=10"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            news = []
            for item in data.get("data", {}).get("items", []):
                title = item.get("title", "")
                desc = item.get("description", "")[:50]
                if title:
                    news.append({
                        "title": title,
                        "source": "36氪",
                        "summary": desc
                    })
            return news
    except Exception:
        pass
    return []


def fetch_news_hacker() -> list:
    """获取 Hacker News 头条"""
    try:
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            story_ids = response.json()[:5]
            news = []
            for sid in story_ids:
                story_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                story_resp = requests.get(story_url, timeout=5)
                if story_resp.status_code == 200:
                    story = story_resp.json()
                    title = story.get("title", "")
                    if title:
                        news.append({
                            "title": title,
                            "source": "Hacker News",
                            "url": story.get("url", "")
                        })
            return news
    except Exception:
        pass
    return []


def fetch_news_v2ex() -> list:
    """获取 V2EX 热门话题"""
    try:
        url = "https://www.v2ex.com/api/topics/hot.json"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            news = []
            for item in data[:10]:
                title = item.get("title", "")
                node = item.get("node", {}).get("title", "")
                if title:
                    news.append({
                        "title": title,
                        "source": "V2EX",
                        "tag": node
                    })
            return news
    except Exception:
        pass
    return []


def fetch_news_toutiao() -> list:
    """获取今日头条热榜（通过公共接口）"""
    try:
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            news = []
            for item in data.get("data", [])[:10]:
                title = item.get("Title", "")
                hot_value = item.get("HotValue", "")
                if title:
                    news.append({
                        "title": title,
                        "source": "今日头条",
                        "heat": f"热度: {hot_value}" if hot_value else ""
                    })
            return news
    except Exception:
        pass
    return []


def fetch_all_news() -> list:
    """从多个来源获取新闻"""
    all_news = []

    sources = [
        ("知乎热榜", fetch_news_zhihu),
        ("今日头条", fetch_news_toutiao),
        ("V2EX", fetch_news_v2ex),
        ("36氪", fetch_news_36kr),
        ("Hacker News", fetch_news_hacker),
    ]

    for source_name, fetch_func in sources:
        try:
            news = fetch_func()
            if news:
                all_news.extend(news)
                print(f"  ✓ {source_name}: 获取 {len(news)} 条")
        except Exception as e:
            print(f"  ✗ {source_name}: 获取失败")

    return all_news[:CONFIG["news_limit"]]


def format_news(news_list: list) -> str:
    """格式化新闻列表"""
    if not news_list:
        return "暂无新闻资讯"

    output = []
    for i, news in enumerate(news_list, 1):
        title = news.get("title", "")
        source = news.get("source", "")
        extra = news.get("heat", news.get("summary", news.get("tag", "")))

        line = f"  {i:2d}. [{source}] {title}"
        if extra:
            line += f" ({extra})"
        output.append(line)

    return "\n".join(output)


# ============================================================
# 日期与宜忌模块
# ============================================================
def get_date_info() -> dict:
    """获取日期信息"""
    now = datetime.now()

    # 星期几
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday = weekdays[now.weekday()]

    # 农历（简化版，实际可接入农历API）
    # 这里使用简化的信息
    lunar_months = ["正月", "二月", "三月", "四月", "五月", "六月",
                    "七月", "八月", "九月", "十月", "冬月", "腊月"]

    # 节日/节气提示
    festivals = get_festivals(now)

    return {
        "date": now.strftime("%Y年%m月%d日"),
        "weekday": weekday,
        "is_weekend": now.weekday() >= 5,
        "festivals": festivals,
        "hour": now.hour,
    }


def get_festivals(date: datetime) -> list:
    """获取近期节日/纪念日"""
    month_day = (date.month, date.day)
    festival_map = {
        (1, 1): "元旦",
        (2, 14): "情人节",
        (3, 8): "妇女节",
        (3, 12): "植树节",
        (4, 1): "愚人节",
        (5, 1): "劳动节",
        (5, 4): "青年节",
        (6, 1): "儿童节",
        (7, 1): "建党节",
        (8, 1): "建军节",
        (9, 10): "教师节",
        (10, 1): "国庆节",
        (12, 25): "圣诞节",
        (12, 31): "跨年夜",
    }

    festivals = []
    if month_day in festival_map:
        festivals.append(festival_map[month_day])

    return festivals


# ============================================================
# 活动推荐模块
# ============================================================
def get_weather_type(data: dict) -> str:
    """判断天气类型"""
    if not data:
        return "unknown"

    current = data.get("current_condition", [{}])[0]
    weather_code = current.get("weatherCode", "")
    temp = int(current.get("temp_C", "20"))

    # 天气代码分类
    # https://www.weatherapi.com/docs/weather_conditions.json
    rain_codes = {"176", "263", "266", "293", "296", "299", "302", "305", "308", "311", "314", "353", "356", "359"}
    snow_codes = {"179", "182", "185", "227", "230", "323", "326", "329", "332", "335", "338", "350", "362", "365", "368", "371", "374", "377"}
    storm_codes = {"200", "386", "389", "392", "395"}
    cloudy_codes = {"116", "119", "122"}

    if weather_code in rain_codes:
        return "rainy"
    elif weather_code in snow_codes:
        return "snowy"
    elif weather_code in storm_codes:
        return "stormy"
    elif weather_code in cloudy_codes:
        return "cloudy"
    else:
        if temp > 30:
            return "hot"
        elif temp < 5:
            return "cold"
        return "sunny"


def get_activity_recommendations(weather_type: str, date_info: dict) -> list:
    """根据天气和日期推荐活动"""
    recommendations = []
    is_weekend = date_info["is_weekend"]
    hour = date_info["hour"]

    # 通用推荐
    general = [
        "📖 阅读一本好书，充实自己",
        "📝 写日记或周报，回顾最近的收获",
        "🧘 冥想10分钟，放松身心",
        "📱 整理手机相册和文件",
        "🎯 制定本周目标和计划",
        "💻 学习一个新技能或工具",
        "📞 给许久未联系的朋友打个电话",
        "🎵 听一张新专辑或新播客",
    ]

    # 根据天气推荐
    weather_activities = {
        "sunny": [
            "🚶 去公园散步或慢跑",
            "📸 户外摄影，记录美好瞬间",
            "🚴 骑自行车探索城市",
            "🧺 和朋友去野餐",
            "⛳ 打高尔夫或网球",
            "🏊 去游泳池游泳",
        ],
        "cloudy": [
            "🚶 天气凉爽，适合户外散步",
            "🏛️ 参观博物馆或展览",
            "☕ 找一家咖啡店看书",
            "🎨 去美术馆或画廊",
        ],
        "rainy": [
            "🎬 看一部经典电影",
            "🍲 在家做一顿美食",
            "📚 去图书馆或书店",
            "🎮 玩一款新游戏",
            "🧹 整理房间，断舍离",
            "🎧 听音乐或播客",
        ],
        "snowy": [
            "⛄ 堆雪人、打雪仗",
            "🍲 煮一锅热汤或火锅",
            "📷 雪景摄影",
            "🧶 做手工或编织",
        ],
        "stormy": [
            "🏠 在家休息，注意安全",
            "📺 追一部新剧",
            "📖 阅读或写作",
            "🧘 做室内瑜伽或健身",
        ],
        "hot": [
            "🏊 去游泳消暑",
            "🍧 做一些冷饮甜品",
            "🏢 去商场或室内场所",
            "🌅 选择清晨或傍晚出行",
        ],
        "cold": [
            "🍲 吃火锅或热汤暖身",
            "☕ 喝一杯热巧克力",
            "🏋️ 去健身房锻炼",
            "🧖 泡温泉或热水澡",
        ],
    }

    # 根据时间段推荐
    time_activities = []
    if 5 <= hour < 9:
        time_activities = [
            "🌅 早起看日出",
            "🏃 晨跑锻炼",
            "🥗 吃一顿营养早餐",
        ]
    elif 9 <= hour < 12:
        time_activities = [
            "☕ 上午适合处理重要工作",
            "📧 查看并回复邮件",
            "📋 制定今日待办事项",
        ]
    elif 12 <= hour < 14:
        time_activities = [
            "🍜 好好吃一顿午餐",
            "😴 午休15-30分钟",
        ]
    elif 14 <= hour < 18:
        time_activities = [
            "☕ 下午茶时间",
            "📊 处理下午的工作任务",
            "🤝 约见朋友或同事",
        ]
    elif 18 <= hour < 21:
        time_activities = [
            "🍽️ 享受晚餐时光",
            "🚶 饭后散步消食",
            "📺 看一部纪录片",
        ]
    else:
        time_activities = [
            "📖 睡前阅读",
            "🧘 做放松冥想",
            "📝 写明日计划",
        ]

    # 周末特殊推荐
    if is_weekend:
        weekend_activities = [
            "🎉 周末愉快！可以睡个懒觉",
            "👨‍👩‍👧 和家人共度时光",
            "🚗 来一次短途旅行",
            "🎨 培养一个新爱好",
        ]
        recommendations.extend(weekend_activities)

    # 合并推荐
    recommendations.extend(time_activities)
    recommendations.extend(weather_activities.get(weather_type, []))

    # 随机添加一些通用推荐
    recommendations.extend(random.sample(general, min(3, len(general))))

    # 随机打乱并限制数量
    random.shuffle(recommendations)
    return recommendations[:8]


# ============================================================
# 早安问候语
# ============================================================
def get_greeting(hour: int, weekday: str) -> str:
    """根据时间生成问候语"""
    greetings = []

    if 5 <= hour < 9:
        greetings = [
            f"早安！新的一天开始了，{weekday}加油！☀️",
            f"早上好！{weekday}，元气满满的一天！💪",
            f"美好的{weekday}早晨，愿你拥有好心情！🌸",
        ]
    elif 9 <= hour < 12:
        greetings = [
            f"上午好！{weekday}，今天也要加油哦！💪",
            f"好巧，{weekday}的上午见到你！☕",
        ]
    elif 12 <= hour < 14:
        greetings = [
            f"中午好！{weekday}，记得吃午饭哦！🍜",
        ]
    elif 14 <= hour < 18:
        greetings = [
            f"下午好！{weekday}，继续加油！🍵",
        ]
    else:
        greetings = [
            f"晚上好！{weekday}，辛苦了一天！🌙",
            f"夜晚好！{weekday}，注意休息哦！✨",
        ]

    return random.choice(greetings)


# ============================================================
# 一句名言
# ============================================================
def get_daily_quote() -> str:
    """每日名言"""
    quotes = [
        ("生活不止眼前的苟且，还有诗和远方。", "高晓松"),
        ("不积跬步，无以至千里；不积小流，无以成江海。", "荀子"),
        ("千里之行，始于足下。", "老子"),
        ("学而不思则罔，思而不学则殆。", "孔子"),
        ("天行健，君子以自强不息。", "周易"),
        ("路漫漫其修远兮，吾将上下而求索。", "屈原"),
        ("业精于勤，荒于嬉；行成于思，毁于随。", "韩愈"),
        ("纸上得来终觉浅，绝知此事要躬行。", "陆游"),
        ("问渠那得清如许，为有源头活水来。", "朱熹"),
        ("宝剑锋从磨砺出，梅花香自苦寒来。", "警世贤文"),
        ("The only way to do great work is to love what you do.", "Steve Jobs"),
        ("Stay hungry, stay foolish.", "Steve Jobs"),
        ("The best time to plant a tree was 20 years ago. The second best time is now.", "Chinese Proverb"),
        ("In the middle of difficulty lies opportunity.", "Albert Einstein"),
        ("Success is not final, failure is not fatal: it is the courage to continue that counts.", "Winston Churchill"),
    ]

    quote, author = random.choice(quotes)
    return f'"{quote}" —— {author}'


# ============================================================
# 主程序
# ============================================================
def print_banner():
    """打印标题横幅"""
    C = Colors if CONFIG["colorful"] else type('NoColor', (), {k: '' for k in dir(Colors) if not k.startswith('_')})()

    banner = f"""
{C.CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     ☀️  每 日 早 报 系 统  ☀️                              ║
║     Daily Morning Briefing System                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{C.END}
"""
    print(banner)


def print_section(title: str, content: str):
    """打印一个带标题的内容区域"""
    C = Colors if CONFIG["colorful"] else type('NoColor', (), {k: '' for k in dir(Colors) if not k.startswith('_')})()

    print(f"\n{C.BOLD}{C.BLUE}{'─' * 50}{C.END}")
    print(f"{C.BOLD}{C.GREEN}  {title}{C.END}")
    print(f"{C.BOLD}{C.BLUE}{'─' * 50}{C.END}")
    print(content)


def generate_briefing():
    """生成完整的每日早报"""
    C = Colors if CONFIG["colorful"] else type('NoColor', (), {k: '' for k in dir(Colors) if not k.startswith('_')})()

    # 打印横幅
    print_banner()

    # 1. 日期信息
    date_info = get_date_info()
    print(f"{C.BOLD}{C.YELLOW}📅 {date_info['date']} {date_info['weekday']}{C.END}")
    if date_info["festivals"]:
        print(f"{C.RED}🎉 今天是: {', '.join(date_info['festivals'])}{C.END}")

    # 2. 早安问候
    greeting = get_greeting(date_info["hour"], date_info["weekday"])
    print(f"\n{C.CYAN}{greeting}{C.END}")

    # 3. 每日名言
    print_section("💡 每日名言", get_daily_quote())

    # 4. 天气信息
    print(f"\n{C.BOLD}🌐 正在获取天气信息...{C.END}")
    weather_data = fetch_weather(CONFIG["city"])
    weather_type = get_weather_type(weather_data)
    print_section("🌤️ 今日天气", format_weather(weather_data))

    # 5. 新闻资讯
    print(f"\n{C.BOLD}📰 正在获取最新资讯...{C.END}")
    news = fetch_all_news()
    print_section("📰 今日资讯", format_news(news))

    # 6. 活动推荐
    recommendations = get_activity_recommendations(weather_type, date_info)
    rec_text = "\n".join([f"  {i+1}. {rec}" for i, rec in enumerate(recommendations)])
    print_section("🎯 今日推荐", rec_text)

    # 7. 结束语
    print(f"\n{C.CYAN}{'═' * 50}{C.END}")
    print(f"{C.BOLD}{C.GREEN}  祝你拥有美好的一天！{C.END}")
    print(f"{C.CYAN}{'═' * 50}{C.END}\n")


def main():
    """主函数"""
    # 支持命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--no-color":
            CONFIG["colorful"] = False
            Colors.disable()
        elif sys.argv[1] == "--city" and len(sys.argv) > 2:
            CONFIG["city"] = sys.argv[2]
        elif sys.argv[1] in ["--help", "-h"]:
            print("每日早报系统 - Daily Morning Briefing")
            print("\n用法: python daily_briefing.py [选项]")
            print("\n选项:")
            print("  --no-color    禁用彩色输出")
            print("  --city CITY   设置城市 (拼音，如 Beijing, Shanghai)")
            print("  --help        显示帮助信息")
            return

    try:
        generate_briefing()
    except KeyboardInterrupt:
        print("\n\n已取消。")
    except Exception as e:
        print(f"\n{Colors.RED}❌ 发生错误: {e}{Colors.END}")
        print("请检查网络连接后重试。")


if __name__ == "__main__":
    main()
