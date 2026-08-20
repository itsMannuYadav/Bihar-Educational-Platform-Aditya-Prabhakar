from typing import Protocol


class PresentationExportProvider(Protocol):
    """docs/01-architecture.md §4's provider seam for decks.

    `NativePptxProvider` is the only implementation for MVP; a
    `CanvaExportProvider` is gated on partnership/API access (docs/07-roadmap.md
    Phase 6) and must be addable without touching the generation graph — which
    is why the graph stores a provider-agnostic slide list and only this layer
    knows what a .pptx is.
    """

    #: File extension without the dot, e.g. "pptx".
    extension: str
    #: MIME type for the download response.
    media_type: str

    def render(self, *, title: str, slides: list[dict]) -> bytes: ...
