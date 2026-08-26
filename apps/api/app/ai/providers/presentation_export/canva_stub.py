class CanvaExportProvider:
    """Stub satisfying the PresentationExportProvider Protocol.

    Full implementation is gated on Canva partnership / API access
    (docs/07-roadmap.md Phase 6). The stub wires in cleanly so the
    generation graph never needs to change when the real provider is ready —
    only the DI binding in `apps/api/app/api/v1/deps.py` changes.
    """

    extension = "pptx"
    media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    def render(self, *, title: str, slides: list[dict]) -> bytes:
        raise NotImplementedError(
            "CanvaExportProvider is not yet implemented. "
            "Use NativePptxProvider for MVP export. "
            "See docs/07-roadmap.md Phase 6 for Canva integration prerequisites."
        )
