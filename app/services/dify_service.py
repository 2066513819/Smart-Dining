import json
import logging

import requests
import time
from app.config import settings
from typing import Dict, Any, Optional, Tuple
from requests.exceptions import ReadTimeout, ConnectTimeout

logger = logging.getLogger(__name__)


class DifyService:
    """Dify AI服务客户端，用于调用Dify API获取餐饮推荐"""

    def __init__(self, is_analysis: bool = False):
        # 根据是否为菜品分析选择不同的API密钥和配置
        if is_analysis:
            # 菜品分析智能体配置 - 从环境变量读取
            self.api_key = getattr(settings, 'DIFY_ANALYSIS_API_KEY', None)
            if not self.api_key:
                raise ValueError("DIFY_ANALYSIS_API_KEY环境变量未配置")
            self.app_id = getattr(settings, 'DIFY_ANALYSIS_APP_ID', 'dish-analysis-app')
            self.base_url = getattr(settings, 'DIFY_ANALYSIS_API_URL', 'http://localhost/v1')
        else:
            # 使用正确的Dify配置
            self.api_key = settings.DIFY_API_KEY
            self.app_id = settings.DIFY_APP_ID
            self.base_url = settings.DIFY_API_URL

        # 清理URL，确保格式正确
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]

        # 确保包含/v1版本号
        if '/v1' not in self.base_url:
            self.base_url = f"{self.base_url}/v1"

        # 从开发手册URL /app/[id]/develop 可以看出，这是一个聊天应用（开发模式），不是工作流应用
        self.is_workflow = False

        # 根据应用类型选择正确的端点
        if self.is_workflow:
            # 工作流API端点
            self.endpoint = f"{self.base_url}/workflows/run"
        else:
            # 聊天API端点
            self.endpoint = f"{self.base_url}/chat-messages"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        logger.debug(f"DifyService初始化完成: app_id={self.app_id}, endpoint={self.endpoint}")

    def validate_config(self) -> Dict[str, Any]:
        """验证Dify配置是否正确"""
        token = self.api_key or ""
        token_type = "app" if token.startswith("app-") else ("sk" if token.startswith("sk-") else "unknown")
        ok_api_key = bool(token)
        ok_base = bool(self.base_url)
        host_part = ""
        try:
            host_part = self.base_url.split("//", 1)[-1].split("/")[0] if self.base_url else ""
        except Exception:
            host_part = ""
        has_port = ":" in host_part
        has_v1 = "/v1" in (self.base_url or "")
        localhost = "localhost" in (self.base_url or "")
        issues = []
        if not ok_api_key:
            issues.append("missing_api_key")
        if token_type == "unknown":
            issues.append("invalid_token_prefix")
        if not ok_base:
            issues.append("missing_base_url")
        if not has_v1:
            issues.append("base_url_missing_v1")
        if localhost and not has_port:
            issues.append("localhost_missing_port")
        if not self.app_id:
            issues.append("missing_app_id")
        return {
            "ok": len(issues) == 0,
            "token_type": token_type,
            "base_url": self.base_url,
            "app_id": self.app_id,
            "issues": issues
        }

    def get_recommendation(self, query: str, user_id: str) -> Dict[str, Any]:
        """
        调用Dify API获取餐饮推荐

        Args:
            query: 查询内容
            user_id: 用户ID

        Returns:
            Dify API响应结果

        Raises:
            ValueError: 参数验证失败
            Exception: API调用失败
        """
        # 1. 验证必要参数
        if not query:
            raise ValueError("查询内容不能为空")
        if not user_id:
            raise ValueError("用户ID不能为空")

        # 根据 token 类型优先选择端点：
        # app- token 通常用于 chat-messages；其他 token 再尝试 completion-messages 兼容。
        token = self.api_key or ""
        if token.startswith("app-"):
            endpoints_to_try = [f"{self.base_url}/chat-messages"]
        else:
            endpoints_to_try = [
                f"{self.base_url}/chat-messages",
                f"{self.base_url}/completion-messages"
            ]

        last_error = None

        for attempt in range(2):
            for endpoint in endpoints_to_try:
                try:
                    response_data = self._try_endpoints(endpoint, query, user_id, attempt)
                    if response_data:
                        return response_data

                except Exception as e:
                    last_error = e
                    logger.warning(f"端点 {endpoint} 调用失败: {str(e)}")
                    continue

        # 所有尝试都失败
        raise Exception(f"智能体回复失败：所有API端点均请求失败。最后错误: {str(last_error)}")

    def _try_endpoints(self, endpoint: str, query: str, user_id: str, attempt: int) -> Optional[Dict[str, Any]]:
        """尝试调用指定端点"""
        base_payload = {
            "inputs": {},
            "query": query,
            "response_mode": "blocking",
            "conversation_id": "",
            "user": user_id,
            "files": []
        }

        payload_variants = [
            { **base_payload },
            { **base_payload, "app_id": self.app_id }
        ]

        response = None
        for payload in payload_variants:
            try:
                response = requests.post(endpoint, json=payload, headers=self.headers, timeout=60)
            except (ReadTimeout, ConnectTimeout) as e:
                raise Exception(f"请求超时: {str(e)}")

            text_lower = (response.text or "").lower()
            if response.status_code == 400 and ('app_unavailable' in text_lower or 'app unavailable' in text_lower) and "app_id" not in payload:
                logger.debug("检测到app_unavailable，尝试改为带app_id的payload")
                continue
            break

        if response.status_code == 200:
            return self._parse_success_response(response)
        elif response.status_code == 400:
            return self._handle_400_error(response, attempt, endpoint)
        else:
            raise Exception(f"API请求失败，状态码: {response.status_code}")

    def _parse_success_response(self, response: requests.Response) -> Dict[str, Any]:
        """解析成功响应"""
        response_data = response.json()
        full_answer = (
            response_data.get('answer', '') or
            response_data.get('content', '') or
            response_data.get('outputs', {}).get('text', '') or
            response_data.get('result', '')
        )

        if full_answer:
            result = {
                "id": response_data.get('id', ''),
                "conversation_id": response_data.get('conversation_id', ''),
                "role": "assistant",
                "content": full_answer,
                "outputs": {
                    "text": full_answer,
                    "type": "text"
                }
            }
            return result
        else:
            logger.debug("未获取到有效answer")
            return None

    def _handle_400_error(self, response: requests.Response, attempt: int, endpoint: str) -> Optional[Dict[str, Any]]:
        """处理400错误"""
        error_text = response.text[:500]

        try:
            error_data = response.json()
            error_message = error_data.get('message', error_data.get('detail', '未知错误'))
            logger.error(f"API请求失败: 400, 错误: {error_message}")
        except:
            logger.error(f"API请求失败: 400, 响应: {error_text[:200]}")

        # 检查是否是模型服务器不可用或连接超时
        is_server_error = any(kw in error_text for kw in ["Server Unavailable Error", "ConnectTimeoutError", "Max retries exceeded"])

        error_text_lower = (error_text or "").lower()
        if 'app_unavailable' in error_text_lower or 'app unavailable' in error_text_lower or is_server_error:
            if attempt < 1 and not is_server_error:
                logger.debug("检测到应用不可用，重试")
                time.sleep(1)
                return None

            friendly = "获取推荐失败：智能体模型服务当前不可用（连接超时）。这通常是后端大模型服务（如 Ollama）未启动或网络连接问题导致的。请稍后重试，或切换到「手动添加」模式。"

            return {
                "role": "assistant",
                "content": friendly,
                "outputs": {
                    "text": friendly,
                    "type": "text"
                },
                "error": {
                    "code": "model_server_unavailable" if is_server_error else "app_unavailable",
                    "status": 400
                }
            }
        else:
            raise Exception(f"Dify API返回400错误。请检查API配置。错误详情: {error_text[:200]}")
