import QtQuick
import QtTest
import "../plasmoid/contents/ui/MeterIntake.js" as MeterIntake

TestCase {
    name: "CommandAndTimes"

    function test_collector_command_quotes_spaces() {
        var bin = "/home/jane doe/.local/bin/ai-usage"
        var cmd = MeterIntake.collectorCommandForBin(bin, "codex")
        compare(cmd, "'/home/jane doe/.local/bin/ai-usage' status codex --json")
        compare(MeterIntake.providerIdFromCommand(cmd), "codex")
    }

    function test_collector_command_quotes_single_quote_and_status_word() {
        var bin = "/home/o'brien status/.local/bin/ai-usage"
        var cmd = MeterIntake.collectorCommandForBin(bin, "stepfun")
        compare(cmd, "'/home/o'\\''brien status/.local/bin/ai-usage' status stepfun --json")
        compare(MeterIntake.providerIdFromCommand(cmd), "stepfun")
    }

    function test_relative_reset_advances_with_time() {
        var resetIso = "2026-11-27T20:00:00Z"
        var t1 = Date.parse("2026-11-27T18:00:00Z")
        var t2 = Date.parse("2026-11-27T19:15:00Z")
        compare(MeterIntake.formatRelative(resetIso, t1), "2h 0m")
        compare(MeterIntake.formatRelative(resetIso, t2), "45m")
    }

    function test_fetched_at_age_advances_with_time() {
        var fetchedIso = "2026-11-27T18:00:00Z"
        var t1 = Date.parse("2026-11-27T18:00:20Z")
        var t2 = Date.parse("2026-11-27T18:07:00Z")
        var t3 = Date.parse("2026-11-27T19:05:00Z")
        compare(MeterIntake.formatFetchedAt(fetchedIso, t1), "just now")
        compare(MeterIntake.formatFetchedAt(fetchedIso, t2), "7m ago")
        compare(MeterIntake.formatFetchedAt(fetchedIso, t3), "1h 5m ago")
    }
}
