class ToolError(Exception):
    pass


class CalculatorError(ToolError):
    pass


class WeatherError(ToolError):
    pass


class WikipediaError(ToolError):
    pass


class LLMError(Exception):
    pass
