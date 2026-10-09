import QtQuick
import QtTest
import "../plasmoid/contents/ui/MeterIntake.js" as Intake

TestCase {
    name: "MeterIntake"

    function test_meters_win_and_do_not_borrow_reset() {
        var rows = Intake.intakeMeters({
            remainingPercent: 10,
            resetAt: "2026-10-09T14:00:00+00:00",
            meters: [
                { label: "Current session", remainingPercent: 99, resetAt: "2026-10-09T14:00:00+00:00" },
                { label: "Current week (all models)", remainingPercent: 78 },
                { label: "Opus limit", remainingPercent: 40, resetAt: "2026-10-12T02:00:00+00:00" }
            ],
            breakdown: [
                { label: "Ignored", remainingPercent: 1, resetAt: "2026-01-01T00:00:00+00:00" }
            ]
        })
        compare(rows.length, 3)
        compare(rows[0].label, "Current session")
        compare(rows[0].remainingPercent, 99)
        compare(rows[0].resetAt, "2026-10-09T14:00:00+00:00")
        compare(rows[1].label, "Current week (all models)")
        compare(rows[1].remainingPercent, 78)
        compare(rows[1].resetAt, "")
        compare(rows[2].label, "Opus limit")
        compare(rows[2].resetAt, "2026-10-12T02:00:00+00:00")
    }

    function test_breakdown_fallback_keeps_own_resets() {
        var rows = Intake.intakeMeters({
            remainingPercent: 84,
            resetAt: "2026-04-30T12:00:00+02:00",
            breakdown: [
                { label: "5-Hour Usage", remainingPercent: 84, resetAt: "2026-04-30T12:00:00+02:00" },
                { label: "Weekly Usage", remainingPercent: 62 }
            ]
        })
        compare(rows.length, 2)
        compare(rows[1].label, "Weekly Usage")
        compare(rows[1].resetAt, "")
    }

    function test_primary_secondary_fallback_has_no_secondary_label() {
        var rows = Intake.intakeMeters({
            remainingPercent: 94,
            secondaryRemainingPercent: 80,
            resetAt: "2026-08-17T12:00:00+02:00"
        })
        compare(rows.length, 2)
        compare(rows[0].label, "Usage limit")
        compare(rows[0].resetAt, "2026-08-17T12:00:00+02:00")
        compare(rows[1].label, "Usage limit")
        compare(rows[1].remainingPercent, 80)
        compare(rows[1].resetAt, "")
        compare(rows[0].label.indexOf("Primary"), -1)
        compare(rows[1].label.indexOf("Secondary"), -1)
    }

    function test_failure_payload_has_no_meters() {
        var rows = Intake.intakeMeters({
            plan: null,
            remainingPercent: null,
            resetAt: null,
            status: "auth_unavailable",
            error: "Re-authenticate in Claude Code."
        })
        compare(rows.length, 0)
    }
}
