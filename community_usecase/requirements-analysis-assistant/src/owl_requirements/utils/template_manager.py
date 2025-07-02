import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from ..core.exceptions import TemplateError

logger = logging.getLogger(__name__)

class TemplateManager:
    """模板管理器，负责加载和管理文档模板。"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化模板管理器。

        Args:
            config: 配置字典，包含模板相关设置
        """
        self.config = config
        self.template_dir = Path(config.get("template_dir", "templates"))
        self.templates = {}
        self.variables = {}

    async def get_template(self, template_name: str) -> Optional[str]:
        """
        获取指定名称的模板。

        Args:
            template_name: 模板名称

        Returns:
            Optional[str]: 模板内容，如果模板不存在则返回None

        Raises:
            TemplateError: 模板加载失败
        """
        try:
            # 如果模板已加载，直接返回
            if template_name in self.templates:
                return self.templates[template_name]

            # 构建模板文件路径
            template_file = self.template_dir / f"{template_name}.json"
            if not template_file.exists():
                logger.warning(f"模板文件不存在: {template_file}")
                return None

            # 加载模板
            with open(template_file, "r", encoding="utf-8") as f:
                template_data = json.load(f)

            # 验证模板结构
            if not self._validate_template(template_data):
                raise TemplateError(f"模板结构无效: {template_name}")

            # 提取模板内容和变量
            template = template_data["template"]
            variables = template_data.get("variables", {})

            # 存储模板和变量
            self.templates[template_name] = template
            self.variables[template_name] = variables

            return template

        except Exception as e:
            logger.error(f"模板加载失败: {str(e)}")
            raise TemplateError(f"模板加载失败: {str(e)}") from e

    def _validate_template(self, template_data: Dict[str, Any]) -> bool:
        """
        验证模板数据的有效性。

        Args:
            template_data: 模板数据

        Returns:
            bool: 验证是否通过
        """
        required_fields = ["template", "version", "description"]
        if not all(field in template_data for field in required_fields):
            logger.warning(f"模板缺少必要字段: {required_fields}")
            return False

        if not isinstance(template_data["template"], str):
            logger.warning("模板内容必须是字符串")
            return False

        if "variables" in template_data and not isinstance(template_data["variables"], dict):
            logger.warning("变量定义必须是字典格式")
            return False

        return True

    def get_variables(self, template_name: str) -> Dict[str, Any]:
        """
        获取模板的变量定义。

        Args:
            template_name: 模板名称

        Returns:
            Dict[str, Any]: 变量定义字典
        """
        return self.variables.get(template_name, {})

    def format_template(
        self,
        template_name: str,
        variables: Dict[str, Any]
    ) -> Optional[str]:
        """
        使用提供的变量格式化模板。

        Args:
            template_name: 模板名称
            variables: 变量值字典

        Returns:
            Optional[str]: 格式化后的模板内容

        Raises:
            TemplateError: 模板格式化失败
        """
        try:
            template = self.templates.get(template_name)
            if not template:
                logger.warning(f"模板不存在: {template_name}")
                return None

            # 验证变量
            required_vars = self.variables.get(template_name, {})
            missing_vars = [
                var for var in required_vars
                if var not in variables
            ]

            if missing_vars:
                raise TemplateError(
                    f"缺少必要变量: {', '.join(missing_vars)}"
                )

            # 格式化模板
            return template.format(**variables)

        except Exception as e:
            logger.error(f"模板格式化失败: {str(e)}")
            raise TemplateError(f"模板格式化失败: {str(e)}") from e 