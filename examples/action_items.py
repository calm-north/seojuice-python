"""
Action Items — Manage SEO action items programmatically.

Shows how to list, filter, create, and update action items,
plus view summary statistics and group breakdowns.
"""
import os

from seojuice import SEOJuice, auto_paginate

client = SEOJuice(api_key=os.environ["SEOJUICE_API_KEY"])
DOMAIN = "example.com"


def show_summary():
    """Display action item summary statistics."""
    summary = client.get_action_item_summary(DOMAIN)

    print("=== Action Items Summary ===")
    print(f"  Total: {summary['total']}")
    print(f"  Open: {summary['open']}")
    print(f"  Done: {summary['done']}")
    print(f"  Snoozed: {summary['snoozed']}")
    print(f"  Dismissed: {summary['dismissed']}")
    print(f"  Auto-fixed: {summary['auto_fixed']}")
    print(f"  Done this month: {summary['done_this_month']}")
    print(f"  Completion rate: {summary['completion_rate']:.1f}%")
    print(f"  By category: {summary['by_category']}")
    print(f"  By priority: {summary['by_priority']}")

    return summary


def list_open_items():
    """List all open action items, ordered by priority."""
    print("\n=== Open Action Items ===")

    for item in auto_paginate(
        lambda page=1, page_size=50: client.list_action_items(
            DOMAIN, status="open", page=page, page_size=page_size
        ),
    ):
        priority = item.get("priority", "unknown")
        print(f"  [{priority}] #{item['id']}: {item['title']}")
        if item.get("guidance"):
            print(f"         Guidance: {item['guidance'][:100]}")
        if item.get("estimated_effort"):
            print(f"         Effort: {item['estimated_effort']}")


def show_groups():
    """Show action items grouped by category."""
    print("\n=== Action Items by Category ===")

    result = client.get_action_item_groups(DOMAIN)
    for group in result.results:
        print(f"  {group['category']}: {group['count']} items")
        print(f"    Priority distribution: {group['priority_distribution']}")


def create_custom_item():
    """Create a custom action item for manual tracking."""
    item = client.create_action_item(
        DOMAIN,
        title="Review and update cornerstone content",
        description="Our top 5 cornerstone pages haven't been refreshed in 6 months",
        category="content",
        priority="high",
        estimated_effort="4h",
    )
    print(f"\nCreated action item #{item['id']}: {item['title']}")
    return item


def complete_item(item_id):
    """Mark an action item as done."""
    updated = client.update_action_item(DOMAIN, item_id, action="done")
    print(f"Completed #{updated['id']}: {updated['title']}")


def snooze_item(item_id, days=7):
    """Snooze an action item for a number of days."""
    updated = client.update_action_item(
        DOMAIN, item_id, action="snooze", snooze_days=days
    )
    print(f"Snoozed #{updated['id']} for {days} days")


def dismiss_item(item_id):
    """Dismiss an action item."""
    updated = client.update_action_item(DOMAIN, item_id, action="dismiss")
    print(f"Dismissed #{updated['id']}: {updated['title']}")


if __name__ == "__main__":
    # 1. View summary
    show_summary()

    # 2. List open items
    list_open_items()

    # 3. View category groups
    show_groups()

    # 4. Create a custom action item
    item = create_custom_item()

    # 5. Mark it done
    # complete_item(item["id"])

    # 6. Or snooze it
    # snooze_item(item["id"], days=14)
