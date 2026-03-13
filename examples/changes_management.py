"""
Change Management — Programmatic review and automation workflows.

Shows how to triage changes by type, bulk-approve changes,
review and reject specific ones, configure automation settings,
and revert changes that caused problems.
"""
import os

from seojuice import SEOJuice, auto_paginate

client = SEOJuice(api_key=os.environ["SEOJUICE_API_KEY"])
DOMAIN = "example.com"

# Change types that are generally safe to auto-approve
AUTO_APPROVE_TYPES = {
    "meta_description",
    "og_title",
    "og_description",
    "og_image",
    "image_alt",
    "structured_data",
}


def print_stats():
    """Print change statistics overview."""
    stats = client.get_change_stats(DOMAIN)

    print("=== Change Stats ===")
    print("By status:", stats["by_status"])
    print("By type:", stats["by_type"])

    pending = stats["by_status"].get("pending", 0)
    applied = stats["by_status"].get("applied", 0)
    print(f"\nPending review: {pending}, Live on site: {applied}")

    return stats


def triage_pending_changes():
    """Fetch pending changes and split into auto-approvable vs needs-review."""
    auto_approvable = []
    needs_review = []

    for change in auto_paginate(
        lambda page=1, page_size=100: client.list_changes(
            DOMAIN, status="pending", page=page, page_size=page_size
        ),
    ):
        if change["change_type"] in AUTO_APPROVE_TYPES:
            auto_approvable.append(change)
        else:
            needs_review.append(change)

    print(
        f"\nTriaged: {len(auto_approvable)} auto-approvable, "
        f"{len(needs_review)} need review"
    )
    return auto_approvable, needs_review


def bulk_approve(changes, label):
    """Bulk-approve a list of changes."""
    if not changes:
        return

    ids = [c["id"] for c in changes]
    result = client.bulk_change_action(DOMAIN, action="approve", ids=ids)

    msg = f"[{label}] Approved {result['total_succeeded']}/{len(ids)}"
    if result["total_failed"] > 0:
        msg += f" ({result['total_failed']} failed)"
    print(msg)

    for failure in result["failed"]:
        print(f"  Change #{failure['id']}: {failure['error']}")


def review_changes(changes):
    """Review individual changes that need manual attention."""
    for change in changes:
        print(f"\n--- Change #{change['id']} ---")
        print(f"  Type: {change['change_type']}")
        print(f"  Page: {change['page_url']}")
        print(f"  Confidence: {change['confidence_score']}")
        print(f"  Reason: {change['reason']}")
        prev = change.get("previous_value") or "(empty)"
        prop = change.get("proposed_value") or "(empty)"
        print(f"  Current: {prev[:80]}")
        print(f"  Proposed: {prop[:80]}")

        # Reject title tag changes with low confidence
        if (
            change["change_type"] == "title_tag"
            and (change.get("confidence_score") or 0) < 0.7
        ):
            client.reject_change(
                DOMAIN,
                change["id"],
                reason="Low confidence title change — needs manual review",
            )
            print("  -> Rejected (low confidence title)")


def configure_automation():
    """Read and update automation settings."""
    current = client.get_change_settings(DOMAIN)
    print("\n=== Current Automation Settings ===")
    print(f"  Internal links: {current['internal_links_mode']}")
    print(f"  Meta tags: {current['meta_tags_mode']}")
    print(f"  Daily limit: {current['max_changes_per_day']}")

    updated = client.update_change_settings(
        DOMAIN,
        meta_tags_mode="suggest",
        title_tags_mode="suggest",
        max_changes_per_day=50,
        max_changes_per_page_per_day=5,
    )

    print("\n=== Updated Settings ===")
    print(f"  Meta tags: {updated['meta_tags_mode']}")
    print(f"  Daily limit: {updated['max_changes_per_day']}")


def monitor_velocity():
    """Monitor change velocity and alert on backlog."""
    stats = client.get_change_stats(DOMAIN)

    pending = stats["by_status"].get("pending", 0)
    applied = stats["by_status"].get("applied", 0)
    rejected = stats["by_status"].get("rejected", 0)

    if pending > 100:
        print(f"[alert] {pending} pending changes — review queue is growing")

    total = applied + rejected
    if total > 0:
        approval_rate = (applied / total) * 100
        print(f"[velocity] Approval rate: {approval_rate:.1f}%")


if __name__ == "__main__":
    # 1. Overview
    print_stats()

    # 2. Triage pending changes by type
    auto_approvable, needs_review = triage_pending_changes()

    # 3. Auto-approve safe change types
    bulk_approve(auto_approvable, "auto-approvable")

    # 4. Manually review changes that need attention
    review_changes(needs_review)

    # 5. Configure automation settings
    configure_automation()

    # 6. Revert a specific change that caused issues
    # client.revert_change(DOMAIN, 12345, reason="Caused 404 — original was correct")

    # 7. Monitor velocity
    monitor_velocity()
