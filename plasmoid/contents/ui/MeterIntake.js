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

// Compact panel and tooltip. Both read intake rows (label + remainingPercent).
// A meter at 0 counts as exhausted and does not pull the headline to 0 while
// another meter still has remaining quota.

var errorTextLimit = 120

function usableMeters(provider) {
    if (!provider || typeof provider !== "object")
        return []
    var status = provider.statusCode || ""
    if (status !== "ok" && status !== "stale")
        return []
    if (!Array.isArray(provider.meters))
        return []
    var rows = []
    for (var i = 0; i < provider.meters.length; i++) {
        var meter = provider.meters[i]
        if (!meter || !finiteNumber(meter.remainingPercent) || meter.remainingPercent < 0)
            continue
        rows.push(meter)
    }
    return rows
}

function compactText(providers) {
    if (!providers || providers.length === 0)
        return "AI"

    var meters = []
    for (var i = 0; i < providers.length; i++) {
        var rows = usableMeters(providers[i])
        for (var j = 0; j < rows.length; j++)
            meters.push(rows[j])
    }

    if (meters.length === 0) {
        var anyAuth = false
        var anyErr = false
        for (var p = 0; p < providers.length; p++) {
            var status = providers[p].statusCode || ""
            if (status === "auth_unavailable")
                anyAuth = true
            if (status !== "idle" && status !== "ok" && status !== "")
                anyErr = true
        }
        if (anyAuth)
            return "AI !"
        if (anyErr)
            return "AI —"
        return "AI …"
    }

    var atZero = 0
    var lowestAbove = null
    for (var m = 0; m < meters.length; m++) {
        if (meters[m].remainingPercent === 0) {
            atZero++
        } else if (lowestAbove === null || meters[m].remainingPercent < lowestAbove) {
            lowestAbove = meters[m].remainingPercent
        }
    }
    if (atZero === meters.length)
        return "AI 0%"
    if (atZero > 0)
        return "AI " + lowestAbove + "% · " + atZero + " at 0%"
    return "AI " + lowestAbove + "%"
}

function oneLine(text, limit) {
    var flat = String(text == null ? "" : text).replace(/\s+/g, " ").replace(/^\s+|\s+$/g, "")
    if (flat.length <= limit)
        return flat
    return flat.substring(0, limit - 1) + "…"
}

function meterLabel(meter) {
    if (meter && typeof meter.label === "string" && meter.label.length > 0)
        return meter.label
    return "Usage limit"
}

function providerTooltip(provider) {
    var name = (provider && typeof provider.name === "string" && provider.name.length > 0)
        ? provider.name
        : "Provider"
    var rows = usableMeters(provider)
    if (rows.length > 0) {
        var head = name
        if (provider.plan && String(provider.plan).length > 0)
            head += " · " + provider.plan
        if (provider.stale === true) {
            var age = (typeof provider.fetchedAtText === "string") ? provider.fetchedAtText : ""
            head += age.length > 0 ? (" (cached " + age + ")") : " (cached)"
        }
        var lines = [head]
        for (var i = 0; i < rows.length; i++)
            lines.push("  " + meterLabel(rows[i]) + " " + rows[i].remainingPercent + "%")
        return lines.join("\n")
    }

    var statusLabel = ""
    if (provider && typeof provider.statusLabel === "string" && provider.statusLabel.length > 0)
        statusLabel = provider.statusLabel
    else if (provider && provider.inFlight === true)
        statusLabel = "…"
    else
        statusLabel = "—"
    var block = name + "  " + statusLabel
    if (provider && typeof provider.errorText === "string" && provider.errorText.length > 0)
        block += "\n" + oneLine(provider.errorText, errorTextLimit)
    return block
}

function tooltipText(providers) {
    if (!providers || providers.length === 0)
        return "No providers enabled"
    var blocks = []
    for (var i = 0; i < providers.length; i++)
        blocks.push(providerTooltip(providers[i]))
    return blocks.join("\n")
}
