class ResearchVaultError(Exception):
    """Base class for application errors that should map to a clean HTTP response."""


class NotFoundError(ResearchVaultError):
    def __init__(self, resource: str, identifier: object):
        super().__init__(f"{resource} not found: {identifier!r}")
        self.resource = resource
        self.identifier = identifier


class LLMProviderError(ResearchVaultError):
    """Raised when all configured LLM providers fail for a request."""


class IngestionError(ResearchVaultError):
    """Raised when arXiv fetch/parse/index steps fail in a way that should stop a run."""
