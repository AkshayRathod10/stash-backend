# apps/bugs/models.py

import uuid

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------

class SeverityChoices(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class StatusChoices(models.TextChoices):
    OPEN = "open", "Open"
    INVESTIGATING = "investigating", "Investigating"
    RESOLVED = "resolved", "Resolved"


class CategoryChoices(models.TextChoices):
    LANGUAGE = "language", "Language"
    OS = "os", "OS"
    SOFTWARE = "software", "Software"
    NETWORK = "network", "Network"
    HARDWARE = "hardware", "Hardware"
    OTHER = "other", "Other"


# ---------------------------------------------------------------------------
# Tag  (shared, user-scoped — used across multiple modules)
# ---------------------------------------------------------------------------

class Tag(TimeStampedModel):
    """
    Global tag pool owned by a user.
    Reused across Bug, Document, Note, Prompt modules via M2M.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tags",
    )
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#6366f1")  # hex colour

    class Meta:
        db_table = "tags"
        ordering = ["name"]
        unique_together = [("user", "name")]
        indexes = [models.Index(fields=["user", "name"])]

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Bug
# ---------------------------------------------------------------------------

class Bug(TimeStampedModel):
    """
    Core bug record.  Each bug belongs to one user and can carry
    multiple code snippets (BugSnippet) and tags (Tag).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bugs",
    )

    # --- Identity ---
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    solution = models.TextField(blank=True)
    source_url = models.URLField(max_length=2048, blank=True)

    # --- Triage ---
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.OPEN,
        db_index=True,
    )
    severity = models.CharField(
        max_length=20,
        choices=SeverityChoices.choices,
        default=SeverityChoices.MEDIUM,
        db_index=True,
    )

    # --- Context (replaces separate language / framework columns) ---
    category = models.CharField(
        max_length=20,
        choices=CategoryChoices.choices,
        default=CategoryChoices.OTHER,
        db_index=True,
    )
    technology = models.CharField(
        max_length=100,
        blank=True
    )   # e.g. "Python", "Linux", "Nginx"
    environment = models.CharField(
        max_length=255,
        blank=True
    )   # e.g. "Node 18, macOS, production"

    # --- Searchable error text ---
    error_message = models.TextField(blank=True)

    # --- Tags (M2M via explicit through table) ---
    tags = models.ManyToManyField(
        Tag,
        through="BugTag",
        related_name="bugs",
        blank=True,
    )

    class Meta:
        db_table = "bugs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "severity"]),
            models.Index(fields=["user", "category"]),
        ]

    def __str__(self) -> str:
        return self.title


# ---------------------------------------------------------------------------
# BugSnippet  (child table — one bug can have multiple code blocks)
# ---------------------------------------------------------------------------

class BugSnippet(models.Model):
    """
    An individual code block attached to a Bug.

    Keeping language per-snippet allows mixed-language bugs
    (e.g. Python traceback + bash fix command) to syntax-highlight
    correctly in the frontend (Monaco / Shiki / CodeMirror).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bug = models.ForeignKey(
        Bug,
        on_delete=models.CASCADE,
        related_name="snippets"
    )

    label = models.CharField(
        max_length=100,
        blank=True
    )  # e.g. "Broken code", "Fixed version"
    language = models.CharField(
        max_length=50,
        blank=True
    )  # e.g. "python", "bash", "nginx"
    content = models.TextField()
    sort_order = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bug_snippets"
        ordering = ["sort_order", "created_at"]

    def __str__(self) -> str:
        return f"{self.bug.title} — {self.label or 'snippet'}"


# ---------------------------------------------------------------------------
# BugTag  (explicit M2M through table)
# ---------------------------------------------------------------------------

class BugTag(models.Model):
    """
    Explicit through table for Bug ↔ Tag.
    Using an explicit model (instead of implicit M2M) keeps the schema
    transparent and allows future per-association metadata if needed.
    """
    bug = models.ForeignKey(Bug, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        db_table = "bug_tags"
        unique_together = [("bug", "tag")]

    def __str__(self) -> str:
        return f"{self.bug} → {self.tag}"
