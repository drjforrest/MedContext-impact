"""Module registry for MedContext core and add-on modules."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException

from app.core.config import settings


@dataclass(frozen=True)
class ModuleInfo:
    name: str
    display_name: str
    description: str
    category: str  # "core" or "addon"
    enabled: bool
    env_flag: str | None  # None for core (always on)


def get_all_modules() -> list[ModuleInfo]:
    return [
        ModuleInfo(
            name="medgemma",
            display_name="Medical Image Analysis",
            description="MedGemma-powered medical image triage and assessment",
            category="core",
            enabled=True,
            env_flag=None,
        ),
        ModuleInfo(
            name="contextual_alignment",
            display_name="Contextual Authenticity",
            description="LLM alignment analysis and claim veracity assessment",
            category="core",
            enabled=True,
            env_flag=None,
        ),
        ModuleInfo(
            name="reverse_search",
            display_name="Reverse Image Search",
            description="Source verification via SerpAPI",
            category="addon",
            enabled=settings.enable_reverse_search,
            env_flag="ENABLE_REVERSE_SEARCH",
        ),
        ModuleInfo(
            name="provenance",
            display_name="Provenance Tracking",
            description="Blockchain-style hash chain genealogy",
            category="addon",
            enabled=settings.enable_provenance,
            env_flag="ENABLE_PROVENANCE",
        ),
        ModuleInfo(
            name="forensics",
            display_name="Forensics Analysis",
            description="Pixel-level copy-move forensics, EXIF analysis, and semantic forensics",
            category="addon",
            enabled=settings.enable_forensics,
            env_flag="ENABLE_FORENSICS",
        ),
    ]


def get_core_modules() -> frozenset[str]:
    """Return the set of core module names that are always enabled."""
    core_modules: set[str] = set()
    for module in get_all_modules():
        if module.category == "core":
            core_modules.add(module.name)
    return frozenset(core_modules)


def require_module(module_name: str):
    """FastAPI dependency that rejects requests when a module is disabled."""

    def dependency() -> None:
        # Check if it's a core module first (always enabled)
        core_modules = get_core_modules()
        if module_name in core_modules:
            return  # Core modules always pass

        # For addon modules, check if they're in enabled addons
        enabled = settings.get_enabled_addons()
        if module_name not in enabled:
            raise HTTPException(
                status_code=501,
                detail={
                    "error": "feature_disabled",
                    "message": f"{module_name} is disabled",
                },
            )

    return dependency
