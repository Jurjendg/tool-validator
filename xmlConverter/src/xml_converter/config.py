from dataclasses import dataclass
import os


@dataclass(slots=True)
class ValidationConfig:
    api_base_url: str = os.getenv("XML_CONVERTER_API_BASE_URL", "")
    api_token: str = os.getenv("XML_CONVERTER_API_TOKEN", "")


@dataclass(slots=True)
class ExtractConfig:
    validate_xsd: bool = os.getenv("XML_CONVERTER_VALIDATE_XSD", "false").lower() == "true"
