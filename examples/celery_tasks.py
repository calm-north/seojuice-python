"""
Celery task patterns for SEOJuice.

Demonstrates background analysis, periodic decay checks, and PDF report
generation. Uses the sync client — pass IDs/strings to tasks, not objects.

Requirements:
    pip install seojuice celery[redis]

Celery beat schedule (add to your celeryconfig or Django settings):
    CELERY_BEAT_SCHEDULE = {
        "check-content-decay-daily": {
            "task": "examples.celery_tasks.check_content_decay",
            "schedule": crontab(hour=6, minute=0),
            "args": ("example.com",),
        },
    }
"""
from __future__ import annotations

import logging
import os
import time

from celery import Celery

from seojuice import SEOJuice

logger = logging.getLogger(__name__)

app = Celery("seojuice_tasks", broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"))


def _get_client() -> SEOJuice:
    return SEOJuice(os.environ["SEOJUICE_API_KEY"])


@app.task(bind=True, max_retries=3, soft_time_limit=300)
def analyze_page(self, domain: str, url: str) -> dict:
    """Queue a page analysis and poll until complete."""
    with _get_client() as client:
        site = client.website(domain)

        queued = site.analyze(url)
        analysis_id = queued["analysis_id"]
        logger.info("Analysis queued for %s: %s", url, analysis_id)

        for _ in range(60):
            status = site.analysis_status(analysis_id)
            if status.get("status") == "completed":
                logger.info("Analysis complete for %s", url)
                return status
            time.sleep(5)

        logger.warning("Analysis timed out for %s", url)
        return {"status": "timeout", "url": url}


@app.task(soft_time_limit=600)
def check_content_decay(domain: str) -> list[dict]:
    """Periodic task: check for high-severity content decay alerts."""
    with _get_client() as client:
        site = client.website(domain)
        decay = site.content_decay(is_active=True, severity="high")

        alerts = []
        for alert in decay:
            logger.warning(
                "Content decay [%s] %s — severity: %s",
                alert.get("decay_type"),
                alert.get("page_url"),
                alert.get("severity"),
            )
            alerts.append(alert)

        logger.info("Found %d high-severity decay alerts for %s", len(alerts), domain)
        return alerts


@app.task(bind=True, max_retries=2, soft_time_limit=600)
def generate_seo_report(self, domain: str, period: str = "this_month") -> str:
    """Create an SEO report and download the PDF."""
    with _get_client() as client:
        site = client.website(domain)

        created = site.create_report(period)
        report_id = created["report_id"]
        logger.info("Report %s created for %s", report_id, domain)

        pdf_bytes = site.report_pdf(report_id)
        output_path = f"/tmp/seojuice_report_{domain}_{report_id}.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        logger.info("Report saved to %s", output_path)
        return output_path
