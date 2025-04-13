from pathlib import Path
from typing import Dict

import jinja2

from logic_arcade.config.constants import PROMPTS_PATH


class PromptManager:
    """
    A class to manage and load Jinja2 templates from a prompts subfolder.

    Example usage:
    from helios.core.llm import PromptManager

    prompts = PromptManager("twitter_trader")
    template = prompts.system_message.render(name="John")
    # Assuming there's a file twitter_trader/system_message.jinja
    """

    def __init__(self, subfolder: str, root_path: Path = PROMPTS_PATH):
        """
        Initialize a prompt loader for a specific subfolder.

        Args:
            subfolder: Name of the subfolder within prompts directory

        Raises:
            ValueError: If subfolder doesn't exist
        """
        self.subfolder = subfolder
        self.root_path = root_path
        self.template_path = self.root_path / subfolder

        if not self.template_path.exists():
            raise ValueError(
                f"Subfolder '{subfolder}' does not exist in prompt_templates directory"
            )

        self.template_loader = jinja2.FileSystemLoader(self.root_path)
        self.template_env = jinja2.Environment(
            loader=self.template_loader, trim_blocks=True, lstrip_blocks=True
        )
        self._templates: Dict[str, jinja2.Template] = {}

    def __getattr__(self, template_name: str) -> jinja2.Template:
        """
        Load and cache templates on demand when accessed as attributes.

        Args:
            template_name: Name of the template file (without extension)

        Returns:
            Jinja2 Template object

        Raises:
            AttributeError: If template file doesn't exist
        """
        if template_name not in self._templates:
            try:
                template_file = f"{self.subfolder}/{template_name}.jinja"
                self._templates[template_name] = self.template_env.get_template(
                    template_file
                )
            except jinja2.TemplateNotFound:
                raise AttributeError(
                    f"No template file '{template_name}.jinja' found in '{self.subfolder}' subfolder"
                )

        return self._templates[template_name]
