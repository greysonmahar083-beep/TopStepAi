import logging

import pytest

from monitoring import status_reporter


@pytest.fixture
def sample_status():
    return {
        "data_inventory": {
            "timeframes": {
                "1min": {"rows": 20000, "start": "2025-10-20T09:24:00+00:00", "end": "2025-11-07T21:59:00+00:00"},
                "5min": {"rows": 11849, "start": "2025-09-09T23:25:00+00:00", "end": "2025-11-07T21:55:00+00:00"},
            },
            "shortfalls": {
                "timeframes": {
                    "5min": {"actual": 11849, "target": 12000},
                    "1min": {"actual": 20000, "target": 20000},
                }
            },
        }
    }


def test_format_status_message_includes_shortfalls(sample_status):
    message = status_reporter.format_status_message(sample_status)

    assert "TopStepAi Data Inventory" in message
    assert "5min: 11849 rows" in message
    assert "Shortfalls:" in message
    assert "- 5min: 11849/12000" in message
    assert "- 1min:" not in message  # should not include non-shortfall entries


def test_publish_status_report_skips_placeholder(sample_status, caplog):
    caplog.set_level(logging.DEBUG, logger=status_reporter.logger.name)

    status_reporter.publish_status_report(sample_status, {"alerts_slack_webhook": "${ALERTS_SLACK_WEBHOOK}"})

    assert "Slack webhook placeholder detected; skipping post" in caplog.text


def test_publish_status_report_posts_to_slack(sample_status, monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger=status_reporter.logger.name)

    captured = {}

    def fake_post(url, message):
        captured["url"] = url
        captured["message"] = message

    monkeypatch.setenv("ALERTS_SLACK_WEBHOOK", "https://hooks.slack.test/abc123")
    monkeypatch.setattr(status_reporter, "post_to_slack", fake_post)

    status_reporter.publish_status_report(sample_status, {"alerts_slack_webhook": "${ALERTS_SLACK_WEBHOOK}"})

    assert captured["url"] == "https://hooks.slack.test/abc123"
    assert "Posted status summary to Slack" in caplog.text
    assert captured["message"].startswith("TopStepAi Data Inventory")
