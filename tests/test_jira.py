from datetime import UTC

from project_risk_agent.connectors.jira import JiraConnector


def test_jira_normalizes_issue_and_adf_description():
    connector = JiraConnector(
        base_url="https://example.atlassian.net",
        email="user@example.com",
        api_token="token",
    )
    signal = connector.normalize(
        {
            "key": "DEMO-42",
            "fields": {
                "summary": "API delivery delayed",
                "status": {"name": "In Progress"},
                "priority": {"name": "High"},
                "updated": "2026-09-15T12:00:00.000+0000",
                "description": {
                    "type": "doc",
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Blocked by vendor."}]}],
                },
                "assignee": {"displayName": "Synthetic User"},
                "project": {"key": "DEMO"},
            },
        }
    )
    assert signal.id == "jira-DEMO-42"
    assert "API delivery delayed" in signal.content
    assert "Blocked by vendor." in signal.content
    assert signal.project_id == "DEMO"
    assert signal.timestamp.tzinfo == UTC
