"""
每日早报晚报系统 - FastAPI 后端
"""

import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from backend.config import settings
from backend.database import Database
from backend.logger import get_logger
from backend.models import (
    NewsItem, Briefing, Settings,
    NewsListResponse, BriefingListResponse, ApiResponse,
    NewsCategory, BriefingType
)
from backend.services.ai_analyzer import AIAnalyzer
from backend.services.news_aggregator import NewsAggregator
from backend.services.briefing_generator import BriefingGenerator
from backend.services.email_sender import EmailSender
from backend.services.push_notifier import PushNotifier
from backend.services.scheduler import TaskScheduler

# 初始化日志
logger = get_logger("main")
api_logger = get_logger("api")

# 全局服务实例
db = Database()
analyzer = AIAnalyzer()
aggregator = NewsAggregator(db, analyzer)
generator = BriefingGenerator(db, analyzer)
email_sender = EmailSender()
push_notifier = PushNotifier()
scheduler = TaskScheduler(db, aggregator, generator, email_sender, push_notifier)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("=" * 50)
    logger.info("Daily Briefing System Starting...")
    logger.info("=" * 50)

    # 初始化数据库
    await db.init_db()
    logger.info("Database initialized")

    # 启动定时任务
    await scheduler.start()

    logger.info("=" * 50)
    logger.info("System started")
    logger.info(f"  - API: http://{settings.host}:{settings.port}")
    logger.info(f"  - Docs: http://{settings.host}:{settings.port}/docs")
    logger.info("=" * 50)

    yield

    # 关闭时
    await scheduler.stop()
    logger.info("System stopped")


# 创建 FastAPI 应用
app = FastAPI(
    title="每日早报晚报系统",
    description="自动获取财经、科技、半导体、AI等新闻，生成早报晚报",
    version=settings.app_version,
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求/响应日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有 HTTP 请求和响应，附带 request_id 用于链路追踪"""
    # 获取请求信息
    method = request.method
    url = str(request.url)
    path = request.url.path
    client_ip = request.client.host if request.client else "unknown"

    # 跳过静态资源和健康检查的日志
    skip_paths = ["/health", "/favicon.ico", "/assets/"]
    if any(path.startswith(p) for p in skip_paths):
        return await call_next(request)

    # 生成 request_id 并绑定到 logger 上下文
    request_id = str(uuid.uuid4())[:8]
    bound_logger = api_logger.bind(request_id=request_id)

    # 记录请求开始
    start_time = time.time()
    bound_logger.info(f"→ {method} {path} | Client: {client_ip}")

    # 获取请求体（如果有）
    if method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
            if body:
                body_text = body.decode("utf-8")[:500]  # 限制长度
                bound_logger.debug(f"  Request Body: {body_text}")
        except Exception:
            pass

    # 处理请求
    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # 记录响应
        bound_logger.info(
            f"← {method} {path} | Status: {response.status_code} | "
            f"Time: {process_time:.3f}s"
        )

        # 将 request_id 放入响应头，方便前端排查
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        process_time = time.time() - start_time
        bound_logger.error(
            f"✗ {method} {path} | Error: {str(e)} | Time: {process_time:.3f}s"
        )
        raise


# ==================== 新闻相关 API ====================

@app.get("/api/news", response_model=NewsListResponse, tags=["新闻"])
async def get_news(
    category: Optional[str] = Query(None, description="新闻类别"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    order_by: str = Query("importance DESC, created_at DESC", description="排序方式")
):
    """获取新闻列表"""
    offset = (page - 1) * page_size

    # 获取新闻
    news_list = await db.get_news(
        category=category,
        limit=page_size,
        offset=offset,
        order_by=order_by
    )

    # 获取总数
    total = await db.get_news_count(category=category)

    return NewsListResponse(
        total=total,
        items=news_list,
        page=page,
        page_size=page_size
    )


@app.get("/api/news/latest", response_model=List[NewsItem], tags=["新闻"])
async def get_latest_news(
    limit: int = Query(20, ge=1, le=50, description="数量")
):
    """获取最新新闻"""
    return await db.get_latest_news(limit=limit)


@app.get("/api/news/{news_id}", response_model=NewsItem, tags=["新闻"])
async def get_news_detail(news_id: int):
    """获取新闻详情"""
    news = await db.get_news_by_id(news_id)
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    return news


@app.get("/api/news/categories/summary", tags=["新闻"])
async def get_categories_summary():
    """获取各类别新闻数量"""
    categories = {}
    for category in NewsCategory:
        count = await db.get_news_count(category=category.value)
        categories[category.value] = {
            "name": category.name,
            "count": count
        }
    return categories


@app.post("/api/news/{news_id}/analyze", tags=["新闻"])
async def analyze_news(news_id: int):
    """AI 分析单条新闻"""
    logger.info(f"收到 AI 分析请求: news_id={news_id}")

    news = await db.get_news_by_id(news_id)
    if not news:
        logger.warning(f"新闻不存在: news_id={news_id}")
        raise HTTPException(status_code=404, detail="新闻不存在")

    # 检查 AI 客户端是否可用
    if not analyzer.client:
        logger.warning("AI 客户端未初始化，返回基础分析")
        analyzed = analyzer._rule_based_analysis(news)
        return {
            "success": True,
            "news_id": news_id,
            "category": analyzed.category.value,
            "importance": analyzed.importance,
            "analysis": f"【基础分析】\n\n事件概述：{analyzed.title}\n新闻来源：{analyzed.source}\n新闻类别：{analyzed.category.value}\n重要性评分：{analyzed.importance}/10\n\n提示：AI 服务未配置，请在 .env 文件中配置有效的 AI_API_KEY",
            "ai_available": False
        }

    try:
        logger.info(f"开始 AI 分析: {news.title[:50]}...")

        # 调用 AI 分析
        analyzed = await analyzer.analyze_news(news)

        # 生成详细分析报告
        analysis_prompt = f"""请对以下新闻进行深入分析，给出你的评价和判断：

新闻标题：{analyzed.title}
新闻来源：{analyzed.source}
新闻摘要：{analyzed.summary or '无'}
新闻类别：{analyzed.category.value}
重要性评分：{analyzed.importance}/10

请从以下角度进行分析：
1. 事件概述：简述事件背景
2. 影响分析：对行业/市场/社会的潜在影响
3. 风险提示：可能存在的风险或不确定性
4. 趋势判断：这是否代表某种趋势
5. 投资建议：（如果是财经新闻）对投资者的建议

请用简洁专业的语言回答，不超过300字。"""

        analysis_result = ""
        try:
            logger.info(f"调用 AI API 生成详细分析: client_type={analyzer.client_type}")
            if analyzer.client_type == "anthropic":
                analysis_result = await analyzer._call_anthropic(analysis_prompt)
            else:
                analysis_result = await analyzer._call_openai(analysis_prompt)
            logger.info(f"AI API 返回结果长度: {len(analysis_result) if analysis_result else 0}")
        except Exception as call_error:
            logger.error(f"AI API 调用失败: {type(call_error).__name__}: {call_error}")

        # 如果 AI 分析结果为空，生成基础分析
        if not analysis_result or analysis_result.strip() == "":
            logger.warning(f"AI 返回空结果，使用基础分析: news_id={news_id}")
            analysis_result = f"""【基础分析】

事件概述：{analyzed.title}
新闻来源：{analyzed.source}
新闻类别：{analyzed.category.value}
重要性评分：{analyzed.importance}/10

基础判断：
- 该新闻来源于「{analyzed.source}」，属于{analyzed.category.value}领域
- 重要性评分为 {analyzed.importance}/10
- 建议关注后续发展

提示：AI 服务返回空结果，请检查 .env 文件中的 AI_API_KEY 是否有效"""
            return {
                "success": True,
                "news_id": news_id,
                "category": analyzed.category.value,
                "importance": analyzed.importance,
                "analysis": analysis_result,
                "ai_available": False
            }

        logger.info(f"AI 分析完成: news_id={news_id}")
        return {
            "success": True,
            "news_id": news_id,
            "category": analyzed.category.value,
            "importance": analyzed.importance,
            "analysis": analysis_result,
            "ai_available": True
        }
    except Exception as e:
        logger.error(f"AI 分析失败: {e}")
        # 如果 AI 分析失败，使用规则引擎给出基础分析
        analyzed = analyzer._rule_based_analysis(news)

        basic_analysis = f"""【基础分析】（AI 服务暂时不可用）

事件概述：{analyzed.title}
新闻来源：{analyzed.source}
新闻类别：{analyzed.category.value}
重要性评分：{analyzed.importance}/10

基础判断：
- 该新闻来源于「{analyzed.source}」，属于{analyzed.category.value}领域
- 重要性评分为 {analyzed.importance}/10，{'属于高重要性新闻' if analyzed.importance >= 7 else '属于中等重要性新闻' if analyzed.importance >= 5 else '属于一般性新闻'}
- 建议关注后续发展

错误信息：{str(e)}"""

        return {
            "success": True,
            "news_id": news_id,
            "category": analyzed.category.value,
            "importance": analyzed.importance,
            "analysis": basic_analysis,
            "ai_available": False
        }


# ==================== 早报/晚报 API ====================

@app.get("/api/briefings", response_model=BriefingListResponse, tags=["早报晚报"])
async def get_briefings(
    type: Optional[str] = Query(None, description="类型：morning/evening"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量")
):
    """获取早报/晚报列表"""
    offset = (page - 1) * page_size

    briefings = await db.get_briefings(
        briefing_type=type,
        limit=page_size,
        offset=offset
    )

    return BriefingListResponse(
        total=len(briefings),
        items=briefings
    )


@app.get("/api/briefings/latest", tags=["早报晚报"])
async def get_latest_briefing(
    type: Optional[str] = Query(None, description="类型：morning/evening")
):
    """获取最新的早报/晚报"""
    briefing = await generator.get_latest_briefing(type)
    if not briefing:
        raise HTTPException(status_code=404, detail="暂无早报/晚报")
    return briefing


@app.get("/api/briefings/{briefing_id}", response_model=Briefing, tags=["早报晚报"])
async def get_briefing_detail(briefing_id: int):
    """获取早报/晚报详情"""
    briefing = await db.get_briefing_by_id(briefing_id)
    if not briefing:
        raise HTTPException(status_code=404, detail="早报/晚报不存在")
    return briefing


@app.post("/api/briefings/generate/{type}", tags=["早报晚报"])
async def generate_briefing(type: str):
    """手动生成早报或晚报"""
    if type == "morning":
        briefing = await generator.generate_morning_briefing()
    elif type == "evening":
        briefing = await generator.generate_evening_briefing()
    else:
        raise HTTPException(status_code=400, detail="类型必须是 morning 或 evening")

    return ApiResponse(
        success=True,
        message=f"{type} 生成成功",
        data={"briefing_id": briefing.id}
    )


# ==================== 设置 API ====================

@app.get("/api/settings", response_model=Settings, tags=["设置"])
async def get_settings():
    """获取系统设置（AI 配置从 .env 文件读取）"""
    return await db.get_settings()


@app.put("/api/settings", response_model=Settings, tags=["设置"])
async def update_settings(new_settings: Settings):
    """更新系统设置（AI 配置不保存到数据库，请修改 .env 文件）"""
    await db.save_settings(new_settings)

    # 更新定时任务配置
    await scheduler.update_schedule()

    return new_settings


@app.get("/api/settings/ai", tags=["设置"])
async def get_ai_settings():
    """获取 AI 配置状态（只读，从 .env 文件读取）"""
    return {
        "ai_available": analyzer.client is not None,
        "ai_provider": settings.ai_provider,
        "ai_model": settings.ai_model,
        "ai_base_url": settings.ai_base_url,
        "ai_api_key_set": bool(settings.ai_api_key),
        "message": "AI 配置从 .env 文件读取，如需修改请编辑 .env 文件"
    }


# ==================== 操作 API ====================

@app.post("/api/aggregate", tags=["操作"])
async def trigger_aggregation():
    """手动触发新闻聚合"""
    try:
        await aggregator.aggregate_all()
        return ApiResponse(success=True, message="新闻聚合完成")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send/{type}", tags=["操作"])
async def trigger_send(type: str):
    """手动触发发送"""
    if type == "morning":
        await scheduler.trigger_morning_briefing()
    elif type == "evening":
        await scheduler.trigger_evening_briefing()
    else:
        raise HTTPException(status_code=400, detail="类型必须是 morning 或 evening")

    return ApiResponse(success=True, message=f"{type} 发送完成")


@app.get("/api/scheduler/jobs", tags=["操作"])
async def get_scheduler_jobs():
    """获取定时任务列表"""
    return scheduler.get_jobs()


# ==================== 市场数据 API ====================

from backend.services.market_service import market_service

@app.get("/api/market/overview", tags=["市场数据"])
async def get_market_overview():
    """获取首页市场概览（精选指数+贵金属）"""
    try:
        return await market_service.get_market_overview()
    except Exception as e:
        logger.error(f"获取市场概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/indices", tags=["市场数据"])
async def get_market_indices(market: str = Query("cn", description="市场: cn/us/hk")):
    """获取市场指数"""
    try:
        if market == "cn":
            return await market_service.get_cn_indices()
        elif market == "us":
            return await market_service.get_us_indices()
        elif market == "hk":
            return await market_service.get_hk_indices()
        else:
            raise HTTPException(status_code=400, detail="市场参数无效，支持: cn/us/hk")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取市场指数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/sectors", tags=["市场数据"])
async def get_market_sectors(market: str = Query("cn", description="市场: cn")):
    """获取板块涨跌排行"""
    try:
        if market == "cn":
            return await market_service.get_cn_sectors()
        else:
            return {"rise": [], "fall": []}
    except Exception as e:
        logger.error(f"获取板块排行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/stocks", tags=["市场数据"])
async def get_market_stocks(market: str = Query("cn", description="市场: cn")):
    """获取个股涨跌排行"""
    try:
        if market == "cn":
            return await market_service.get_cn_stocks()
        else:
            return {"rise": [], "fall": []}
    except Exception as e:
        logger.error(f"获取个股排行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/detail", tags=["市场数据"])
async def get_market_detail(market: str = Query("cn", description="市场: cn/us/hk/commodities")):
    """获取市场详情（指数+板块+个股）"""
    try:
        return await market_service.get_market_detail(market)
    except Exception as e:
        logger.error(f"获取市场详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/commodities", tags=["市场数据"])
async def get_commodities():
    """获取贵金属/大宗商品行情"""
    try:
        return await market_service.get_commodities()
    except Exception as e:
        logger.error(f"获取贵金属行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 系统 API ====================

@app.get("/api/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/stats", tags=["系统"])
async def get_stats():
    """获取系统统计"""
    news_count = await db.get_news_count()
    briefings = await db.get_briefings(limit=1000)
    briefing_count = len(briefings)

    return {
        "news_count": news_count,
        "briefing_count": briefing_count,
        "latest_news": await db.get_latest_news(limit=1),
        "latest_briefing": await generator.get_latest_briefing()
    }


@app.post("/api/logs", tags=["系统"])
async def receive_frontend_logs(request: Request):
    """接收前端日志"""
    try:
        body = await request.json()
        logs = body.get("logs", [])

        frontend_logger = get_logger("frontend")

        for log in logs:
            level = log.get("level", "info")
            module = log.get("module", "unknown")
            message = log.get("message", "")
            data = log.get("data")

            # 构建日志消息
            log_message = f"[{module}] {message}"
            if data:
                log_message += f" | {JSON.dumps(data)[:200]}"

            # 根据级别记录日志
            if level == "error":
                frontend_logger.error(log_message)
            elif level == "warn":
                frontend_logger.warning(log_message)
            elif level == "debug":
                frontend_logger.debug(log_message)
            else:
                frontend_logger.info(log_message)

        return {"success": True, "received": len(logs)}
    except Exception as e:
        logger.error(f"Failed to receive frontend logs: {e}")
        return {"success": False, "error": str(e)}


# ==================== 静态文件服务 ====================

# 挂载前端静态文件（如果存在）
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
