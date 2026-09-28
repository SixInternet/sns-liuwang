"""应用配置 — 通过环境变量加载所有配置项"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置，从 .env 文件或环境变量读取"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # 数据库连接
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sns_liuwang"

    # 应用环境
    app_env: str = "development"

    # 服务端口
    app_port: int = 8001

    # JWT 签名密钥
    secret_key: str = "change-me-to-a-random-secret-in-production"

    # CDP 浏览器配置（已废弃，保留用于向后兼容）
    cdp_host: str = "10.1.0.60"
    cdp_port: int = 9333

    # BrowserOS MCP 配置
    browseros_mcp_url: str = "http://10.1.0.60:9777/mcp"
    browseros_transport: str = "streamable-http"

    # DeepSeek API 配置
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"

    # OpenClaw Gateway URL
    openclaw_gateway_url: str = "http://localhost:18789"

    # OpenClaw Gateway auth token
    openclaw_gateway_token: str = ""

    # 单次采集最多入库的信息源数量
    collection_max_sources: int = 10

    @property
    def is_dev(self) -> bool:
        """是否为开发环境"""
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """获取全局配置单例"""
    return Settings()
