class RagError(Exception):
    pass


class LLMNotConfigured(RagError):
    pass


class LLMError(RagError):
    pass