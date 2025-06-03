import yaml
import os
from typing import Dict, Any, Optional
from .interfaces import ConfigManagerInterface
from .exceptions import ConfigurationException


class ConfigManager(ConfigManagerInterface):
    """Configuration manager with YAML support."""

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._config_path: Optional[str] = None

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            if not os.path.exists(config_path):
                raise ConfigurationException(
                    f"Configuration file not found: {config_path}"
                )

            with open(config_path, "r", encoding="utf-8") as file:
                self._config = yaml.safe_load(file) or {}
                self._config_path = config_path

            return self._config

        except yaml.YAMLError as e:
            raise ConfigurationException(f"Invalid YAML configuration: {e}")
        except Exception as e:
            raise ConfigurationException(f"Failed to load configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'camera.width')."""
        keys = key.split(".")
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key.split(".")
        config = self._config

        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the value
        config[keys[-1]] = value

    def save_config(self, config_path: str = None) -> None:
        """Save current configuration to file."""
        path = config_path or self._config_path
        if not path:
            raise ConfigurationException("No configuration file path specified")

        try:
            with open(path, "w", encoding="utf-8") as file:
                yaml.dump(self._config, file, default_flow_style=False, indent=2)
        except Exception as e:
            raise ConfigurationException(f"Failed to save configuration: {e}")

    @property
    def config(self) -> Dict[str, Any]:
        """Get the entire configuration dictionary."""
        return self._config.copy()
