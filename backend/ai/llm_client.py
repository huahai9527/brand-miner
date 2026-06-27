"""
LLM 客户端 — DeepSeek API 封装（OpenAI 兼容协议）

错误处理策略（全部静默降级，永不抛异常）：
  - DEEPSEEK_API_KEY 未配置或为空 → is_available()=False，直接走 Fallback
  - 429 限流 → 记录日志，走 Fallback
  - 请求超时 → 记录日志，走 Fallback
  - 任何网络/解析异常 → 记录日志，走 Fallback，不向上抛出

每次调用记录：耗时、token 消耗、成功/失败
"""
import json
import logging
import time
import os
from typing import AsyncGenerator, Optional
import httpx

from backend.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT, LLM_MAX_TOKENS, LLM_TEMPERATURE

logger = logging.getLogger(__name__)

# 优先使用 DEEPSEEK_API_KEY，其次用通用的 LLM_API_KEY
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "") or LLM_API_KEY


class LLMClient:
    """DeepSeek API 客户端（OpenAI 兼容协议）

    所有公开方法永不抛异常 —— 失败时返回 None（chat）/ 空流（chat_stream）。
    调用方只需判空即可决定是否降级到 Fallback。
    """

    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.base_url = LLM_BASE_URL.rstrip("/")
        self.model = LLM_MODEL
        self.timeout = LLM_TIMEOUT
        self.max_tokens = LLM_MAX_TOKENS
        self.temperature = LLM_TEMPERATURE

    # ── 公开接口 ──

    def is_available(self) -> bool:
        """检查 API Key 是否已配置且非空"""
        return bool(self.api_key and self.api_key.strip() and len(self.api_key.strip()) > 10)

    async def chat(self, messages: list[dict]) -> Optional[str]:
        """
        非流式调用 — 失败自动降级，永不抛异常

        Args:
            messages: OpenAI 格式 [{"role":"system","content":"..."}, ...]

        Returns:
            AI 回复文本；不可用时返回 None → 调用方走 Fallback
        """
        if not self.is_available():
            logger.warning("[LLM] DEEPSEEK_API_KEY 未配置或为空 — 走 Fallback")
            return None

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False,
        }

        start_time = time.perf_counter()
        success = False
        token_usage = 0

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )

                elapsed = round(time.perf_counter() - start_time, 2)

                if resp.status_code == 429:
                    logger.warning(
                        f"[LLM] 429 Too Many Requests | 耗时={elapsed}s | 降级到 Fallback"
                    )
                    return None

                if resp.status_code != 200:
                    err_body = resp.text[:200]
                    logger.warning(
                        f"[LLM] HTTP {resp.status_code} | 耗时={elapsed}s | body={err_body}"
                    )
                    return None

                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                token_usage = data.get("usage", {}).get("total_tokens", 0)
                success = True

                logger.info(
                    f"[LLM] ✓ chat | 耗时={elapsed}s | tokens={token_usage} | "
                    f"入={data['usage'].get('prompt_tokens', '?')} "
                    f"出={data['usage'].get('completion_tokens', '?')}"
                )
                return content

        except httpx.TimeoutException:
            elapsed = round(time.perf_counter() - start_time, 2)
            logger.warning(f"[LLM] 请求超时 | 耗时={elapsed}s | 降级到 Fallback")
            return None
        except Exception as e:
            elapsed = round(time.perf_counter() - start_time, 2)
            logger.warning(f"[LLM] 异常 {type(e).__name__}: {e} | 耗时={elapsed}s | 降级到 Fallback")
            return None

    async def chat_stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """
        流式调用 — 逐 token 输出，失败时静默结束

        Args:
            messages: OpenAI 格式消息列表

        Yields:
            每个 token 的 delta 文本；完全失败时生成器为空
        """
        if not self.is_available():
            logger.warning("[LLM] DEEPSEEK_API_KEY 未配置或为空 — 流式走 Fallback")
            return

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": True,
        }

        start_time = time.perf_counter()
        token_count = 0
        success = False

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                ) as resp:
                    if resp.status_code == 429:
                        elapsed = round(time.perf_counter() - start_time, 2)
                        logger.warning(
                            f"[LLM] 流式 429 Too Many Requests | 耗时={elapsed}s | 降级到 Fallback"
                        )
                        return

                    if resp.status_code != 200:
                        elapsed = round(time.perf_counter() - start_time, 2)
                        logger.warning(
                            f"[LLM] 流式 HTTP {resp.status_code} | 耗时={elapsed}s"
                        )
                        return

                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                token_count += 1
                                yield content
                        except json.JSONDecodeError:
                            continue

            success = True

        except httpx.TimeoutException:
            elapsed = round(time.perf_counter() - start_time, 2)
            logger.warning(f"[LLM] 流式超时 | 耗时={elapsed}s | 已输出 {token_count} tokens")
        except Exception as e:
            elapsed = round(time.perf_counter() - start_time, 2)
            logger.warning(
                f"[LLM] 流式异常 {type(e).__name__}: {e} | 耗时={elapsed}s | 已输出 {token_count} tokens"
            )
        finally:
            elapsed = round(time.perf_counter() - start_time, 2)
            status = "✓" if success else "✗"
            logger.info(
                f"[LLM] {status} chat_stream | 耗时={elapsed}s | "
                f"tokens≈{token_count} | success={success}"
            )


# 全局单例
llm_client = LLMClient()
