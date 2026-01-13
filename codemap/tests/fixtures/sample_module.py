"""Sample Python module for testing."""

from typing import Optional, List


def simple_function(x: int) -> int:
    """A simple function."""
    return x * 2


async def async_function(url: str) -> dict:
    """An async function."""
    return {"url": url}


class BaseClass:
    """A base class."""

    def __init__(self, name: str):
        """Initialize with name."""
        self.name = name

    def get_name(self) -> str:
        """Get the name."""
        return self.name


class DerivedClass(BaseClass):
    """A derived class with more methods."""

    def __init__(self, name: str, value: int = 0):
        """Initialize with name and value."""
        super().__init__(name)
        self.value = value

    def process(self, data: List[str]) -> Optional[str]:
        """Process some data."""
        if not data:
            return None
        return ", ".join(data)

    async def async_method(self, timeout: float = 1.0) -> bool:
        """An async method."""
        return True

    class NestedClass:
        """A nested class."""

        def nested_method(self):
            """Method in nested class."""
            pass


@property
def decorated_property(self) -> str:
    """A decorated property."""
    return "value"


@staticmethod
def static_helper(a: int, b: int) -> int:
    """A static helper function."""
    return a + b
