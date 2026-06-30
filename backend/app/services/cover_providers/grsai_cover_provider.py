"""GrsAI 封面图片 Provider"""
from __future__ import annotations

import base64
from typing import Any

import httpx

from app.logger import get_logger, safe_preview
from app.services.cover_providers.base_cover_provider import BaseCoverProvider, CoverGenerationResult

logger = get_logger(__name__)


class GrsaiCoverProvider(BaseCoverProvider):
    """基于 GrsAI API 的封面生成实现"""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = (base_url or "https://grsaiapi.com/v1").rstrip("/")

    async def generate_cover(
        self,
        *,
        prompt: str,
        model: str,
        width: int,
        height: int,
    ) -> CoverGenerationResult:
        url = f"{self.base_url}/api/generate"
        payload: dict[str, Any] = {
            "model": model or "gpt-image-2",
            "prompt": f"{prompt}\n\nGenerate a vertical book cover image at {width}x{height} pixels.",
            "images": [],
            "aspectRatio": f"{width}x{height}",
            "replyType": "json",
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=headers, json=payload)

            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "GrsAI 封面生成 HTTP 错误: status=%s response=%s",
                exc.response.status_code if exc.response else None,
                safe_preview(exc.response.text, 500) if exc.response is not None else None,
            )
            raise
        except Exception:
            logger.error("GrsAI 封面生成请求异常", exc_info=True)
            raise

        status = data.get("status")
        if status == "running":
            # Async mode - would need polling, but we requested json mode
            raise ValueError("GrsAI 返回异步任务，请稍后重试或联系管理员")
        if status == "violation":
            error_msg = data.get("error", "内容违规")
            raise ValueError(f"GrsAI 内容违规: {error_msg}")
        if status == "failed":
            error_msg = data.get("error", "生成失败")
            raise ValueError(f"GrsAI 生成失败: {error_msg}")
        if status != "succeeded":
            raise ValueError(f"GrsAI 返回未知状态: {status}")

        results = data.get("results") or []
        if not results:
            raise ValueError("GrsAI 未返回生成结果")

        image_url = results[0].get("url")
        if not image_url:
            raise ValueError("GrsAI 结果中没有图片 URL")

        # Download the image from the URL
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                img_response = await client.get(image_url)
                img_response.raise_for_status()
                content = img_response.content
        except Exception as e:
            logger.error(f"GrsAI 图片下载失败: {e}")
            raise ValueError(f"无法下载 GrsAI 生成的图片: {e}")

        # Detect file type from content or default to png
        file_extension = "png"
        mime_type = "image/png"

        # Try to detect from magic bytes
        if content.startswith(b'\xFF\xD8\xFF'):
            file_extension = "jpg"
            mime_type = "image/jpeg"
        elif content.startswith(b'\x89PNG'):
            file_extension = "png"
            mime_type = "image/png"
        elif content.startswith(b'GIF'):
            file_extension = "gif"
            mime_type = "image/gif"

        return {
            "content": content,
            "mime_type": mime_type,
            "file_extension": file_extension,
            "revised_prompt": None,
            "provider": "grsai",
            "model": model,
        }
