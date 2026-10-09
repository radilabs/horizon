import QtQuick
import QtTest
import "../plasmoid/contents/ui/MeterIntake.js" as Intake

TestCase {
    name: "CompactSummary"

    function provider(name, status, meters, extra) {
        var row = {
            name: name,
            statusCode: status,
            plan: "",
            stale: status === "stale",
            fetchedAtText: "",
            statusLabel: "",
            errorText: "",
            inFlight: false,
            meters: meters || []
        }
        if (extra) {
            for (var key in extra)
                row[key] = extra[key]
        }
        return row
    }

    function test_mixed_zero_does_not_hide_remaining() {
        var text = Intake.compactText([
            provider("Codex", "ok", [
                { label: "5-hour limit", remainingPercent: 99 },
                { label: "Weekly limit", remainingPercent: 99 }
            ]),
            provider("Cursor", "ok", [
                { label: "Cursor Models", remainingPercent: 75 },
                { label: "Other Models", remainingPercent: 0 }
            ]),
            provider("StepFun", "ok", [
                { label: "5-Hour Usage", remainingPercent: 97 },
                { label: "Weekly Usage", remainingPercent: 86 }
            ]),
            provider("Claude", "ok", [
                { label: "Current session", remainingPercent: 100 },
                { label: "Current week", remainingPercent: 78 }
            ])
        ])
        compare(text, "AI 75% · 1 at 0%")
    }

    function test_all_healthy_uses_lowest_remaining() {
        var text = Intake.compactText([
            provider("Codex", "ok", [{ label: "5-hour limit", remainingPercent: 99 }]),
            provider("Claude", "ok", [{ label: "Current week", remainingPercent: 78 }])
        ])
        compare(text, "AI 78%")
    }

    function test_every_meter_at_zero() {
        compare(Intake.compactText([
            provider("Cursor", "ok", [
                { label: "Cursor Models", remainingPercent: 0 },
                { label: "Other Models", remainingPercent: 0 }
            ])
        ]), "AI 0%")
    }

    function test_two_exhausted_meters_keep_the_rest() {
        compare(Intake.compactText([
            provider("Cursor", "ok", [
                { label: "Cursor Models", remainingPercent: 40 },
                { label: "Other Models", remainingPercent: 0 }
            ]),
            provider("Claude", "ok", [{ label: "Current week", remainingPercent: 0 }])
        ]), "AI 40% · 2 at 0%")
    }

    function test_stale_meters_count() {
        compare(Intake.compactText([
            provider("Codex", "stale", [{ label: "5-hour limit", remainingPercent: 12 }], {
                fetchedAtText: "3m ago"
            })
        ]), "AI 12%")
    }

    function test_no_providers() {
        compare(Intake.compactText([]), "AI")
    }

    function test_auth_without_quota() {
        compare(Intake.compactText([
            provider("Claude", "auth_unavailable", [], { statusLabel: "Needs authentication" })
        ]), "AI !")
    }

    function test_error_without_quota() {
        compare(Intake.compactText([
            provider("Codex", "upstream_error", [], { statusLabel: "Unavailable" })
        ]), "AI —")
    }

    function test_loading() {
        compare(Intake.compactText([
            provider("Codex", "idle", [], { inFlight: true, statusLabel: "Loading…" })
        ]), "AI …")
    }

    function test_tooltip_lists_meters_plan_and_stale_age() {
        var text = Intake.tooltipText([
            provider("Codex", "ok", [
                { label: "5-hour limit", remainingPercent: 99 },
                { label: "Weekly limit", remainingPercent: 88 }
            ], { plan: "ChatGPT Plus" }),
            provider("Cursor", "stale", [
                { label: "Cursor Models", remainingPercent: 75 },
                { label: "Other Models", remainingPercent: 0 }
            ], { plan: "Pro", fetchedAtText: "4m ago" })
        ])
        compare(text.indexOf("Codex · ChatGPT Plus") >= 0, true)
        compare(text.indexOf("  5-hour limit 99%") >= 0, true)
        compare(text.indexOf("  Weekly limit 88%") >= 0, true)
        compare(text.indexOf("Cursor · Pro (cached 4m ago)") >= 0, true)
        compare(text.indexOf("  Other Models 0%") >= 0, true)
        compare(text.indexOf("Reset") >= 0, false)
        compare(text.indexOf("Secondary") >= 0, false)
    }

    function test_tooltip_failure_includes_shortened_error() {
        var longError = ""
        for (var i = 0; i < 40; i++)
            longError += "unavailable "
        var text = Intake.tooltipText([
            provider("Claude", "auth_unavailable", [], {
                statusLabel: "Needs authentication",
                errorText: longError
            })
        ])
        compare(text.indexOf("Claude  Needs authentication") >= 0, true)
        compare(text.indexOf("…") >= 0, true)
        compare(text.indexOf("\n") >= 0, true)
        var errorLine = text.split("\n")[1]
        verify(errorLine.length <= 120)
    }

    function test_tooltip_empty() {
        compare(Intake.tooltipText([]), "No providers enabled")
    }
}