.pragma library

// Popup meter intake for Phase 8. Percent values are remaining, not used.
// A meter reset is kept only when that meter has its own resetAt.
// The primary/secondary fallback may attach the payload reset to the first row only.

function finiteNumber(value) {
    return typeof value === "number" && isFinite(value)
}

function meterRow(source) {
    if (!source || typeof source !== "object")
        return null
    if (!finiteNumber(source.remainingPercent))
        return null
    var label = ""
    if (typeof source.label === "string")
        label = source.label
    var resetAt = ""
    if (typeof source.resetAt === "string")
        resetAt = source.resetAt
    return {
        label: label,
        remainingPercent: source.remainingPercent,
        resetAt: resetAt
    }
}

function rowsFromList(list) {
    var rows = []
    for (var i = 0; i < list.length; i++) {
        var row = meterRow(list[i])
        if (row)
            rows.push(row)
    }
    return rows
}

function intakeMeters(obj) {
    if (!obj || typeof obj !== "object")
        return []
    if (Array.isArray(obj.meters) && obj.meters.length > 0)
        return rowsFromList(obj.meters)
    if (Array.isArray(obj.breakdown) && obj.breakdown.length > 0)
        return rowsFromList(obj.breakdown)
    if (!finiteNumber(obj.remainingPercent) || obj.remainingPercent < 0)
        return []
    var rows = [{
        label: "Usage limit",
        remainingPercent: obj.remainingPercent,
        resetAt: (typeof obj.resetAt === "string") ? obj.resetAt : ""
    }]
    if (finiteNumber(obj.secondaryRemainingPercent) && obj.secondaryRemainingPercent >= 0) {
        rows.push({
            label: "Usage limit",
            remainingPercent: obj.secondaryRemainingPercent,
            resetAt: ""
        })
    }
    return rows
}
