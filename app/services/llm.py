from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from app.config import get_settings
from typing import Literal
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMService:
    """Service for managing multiple LLM providers."""
    
    def __init__(self):
        self._models = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize available LLM models."""
        # Claude (Primary)
        if settings.anthropic_api_key:
            self._models["claude"] = ChatAnthropic(
                model=settings.primary_model,
                anthropic_api_key=settings.anthropic_api_key,
                temperature=0.7,
                max_tokens=4096
            )
            logger.info(f"Initialized Claude model: {settings.primary_model}")
        
        # OpenAI (Fallback)
        if settings.openai_api_key and settings.fallback_model:
            self._models["openai"] = ChatOpenAI(
                model=settings.fallback_model,
                openai_api_key=settings.openai_api_key,
                temperature=0.7,
                max_tokens=4096
            )
            logger.info(f"Initialized OpenAI model: {settings.fallback_model}")
    
    def get_model(self, provider: Literal["claude", "openai"] = "claude") -> BaseChatModel:
        """
        Get LLM model by provider.
        
        Args:
            provider: The model provider to use
            
        Returns:
            BaseChatModel: The language model instance
            
        Raises:
            ValueError: If provider is not available
        """
        if provider not in self._models:
            raise ValueError(f"Model provider '{provider}' not available. Available: {list(self._models.keys())}")
        
        return self._models[provider]
    
    def get_primary_model(self) -> BaseChatModel:
        """Get the primary model (Claude by default)."""
        return self.get_model("claude")
    
    def get_fallback_model(self) -> BaseChatModel:
        """Get the fallback model (OpenAI if available)."""
        if "openai" in self._models:
            return self.get_model("openai")
        return self.get_primary_model()


# Global instance
llm_service = LLMService()
