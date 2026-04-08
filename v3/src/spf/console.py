"""Set up Rich consoles for SteamPunkFantasy."""

from rich.console import Console

stdout = Console()
stderr = Console(stderr=True)

__all__ = ["stderr", "stdout"]
