import QtQuick
import QtQuick.Layouts
import QtCore
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    Plasmoid.title: "Horizon"
    toolTipMainText: "Horizon"
    toolTipSubText: root.tooltipSummary

    preferredRepresentation: Plasmoid.formFactor === PlasmaCore.Types.Planar
        ? fullRepresentation
        : compactRepresentation

    switchWidth: Kirigami.Units.gridUnit * 12
    switchHeight: Kirigami.Units.gridUnit * 8
    activationTogglesExpanded: true

    readonly property var allProviderIds: ["codex", "cursor", "stepfun"]

    property string compactText: "AI"
    property string tooltipSummary: "AI Agent Usage"
    property bool anyInFlight: false

    ListModel {
        id: providersModel
    }

    function filesystemPath(urlOrPath) {
        var s = String(urlOrPath)
        if (s.indexOf("file://") === 0)
            return decodeURIComponent(s.substring(7))
        return s
    }

    function collectorBin() {
        var home = filesystemPath(StandardPaths.writableLocation(StandardPaths.HomeLocation))
        return home + "/.local/bin/ai-usage"
    }

    function collectorCommand(providerId) {
        return collectorBin() + " status " + providerId + " --json"
    }

    function providerIdFromCommand(cmd) {
        var parts = String(cmd).trim().split(/\s+/)
        var statusIdx = parts.indexOf("status")
        if (statusIdx >= 0 && statusIdx + 1 < parts.length)
            return parts[statusIdx + 1]
        return ""
    }

    function enabledProviderIds() {
        var ids = []
        if (plasmoid.configuration.enableCodex)
            ids.push("codex")
        if (plasmoid.configuration.enableCursor)
            ids.push("cursor")
        if (plasmoid.configuration.enableStepfun)
            ids.push("stepfun")
        return ids
    }

    function providerEnabled(providerId) {
        if (providerId === "codex")
            return plasmoid.configuration.enableCodex
        if (providerId === "cursor")
            return plasmoid.configuration.enableCursor
        if (providerId === "stepfun")
            return plasmoid.configuration.enableStepfun
        return false
    }

    function indexForProvider(providerId) {
        for (var i = 0; i < providersModel.count; i++) {
            if (providersModel.get(i).providerId === providerId)
                return i
        }
        return -1
    }

    function syncModelToEnabled() {
        var enabled = enabledProviderIds()
        var byId = ({})
        for (var i = 0; i < providersModel.count; i++) {
            var row = providersModel.get(i)
            byId[row.providerId] = {
                providerId: row.providerId,
                providerName: row.providerName,
                planName: row.planName,
                remainingPercent: row.remainingPercent,
                secondaryRemainingPercent: row.secondaryRemainingPercent,
                breakdownJson: row.breakdownJson,
                resetText: row.resetText,
                statusCode: row.statusCode,
                statusLabel: row.statusLabel,
                errorText: row.errorText,
                fetchedAtText: row.fetchedAtText,
                stale: row.stale,
                hasQuota: row.hasQuota,
                inFlight: row.inFlight
            }
        }
        providersModel.clear()
        for (var e = 0; e < enabled.length; e++) {
            var id = enabled[e]
            if (byId[id]) {
                providersModel.append(byId[id])
            } else {
                providersModel.append({
                    providerId: id,
                    providerName: id,
                    planName: "",
                    remainingPercent: -1,
                    secondaryRemainingPercent: -1,
                    breakdownJson: "[]",
                    resetText: "",
                    statusCode: "idle",
                    statusLabel: "",
                    errorText: "",
                    fetchedAtText: "",
                    stale: false,
                    hasQuota: false,
                    inFlight: false
                })
            }
        }
        updateAnyInFlight()
        updateCompactSummary()
    }

    function formatRelative(iso) {
        if (!iso)
            return ""
        var ms = Date.parse(iso)
        if (isNaN(ms))
            return iso
        var diffSec = Math.floor((ms - Date.now()) / 1000)
        var sign = ""
        if (diffSec < 0) {
            sign = "-"
            diffSec = -diffSec
        }
        var days = Math.floor(diffSec / 86400)
        var hours = Math.floor((diffSec % 86400) / 3600)
        var mins = Math.floor((diffSec % 3600) / 60)
        if (days > 0)
            return sign + days + "d " + hours + "h"
        if (hours > 0)
            return sign + hours + "h " + mins + "m"
        return sign + mins + "m"
    }

    function formatFetchedAt(iso) {
        if (!iso)
            return ""
        var ms = Date.parse(iso)
        if (isNaN(ms))
            return iso
        var agoSec = Math.max(0, Math.floor((Date.now() - ms) / 1000))
        var days = Math.floor(agoSec / 86400)
        var hours = Math.floor((agoSec % 86400) / 3600)
        var mins = Math.floor((agoSec % 3600) / 60)
        if (days > 0)
            return days + "d " + hours + "h ago"
        if (hours > 0)
            return hours + "h " + mins + "m ago"
        if (mins > 0)
            return mins + "m ago"
        return "just now"
    }

    function friendlyStatusLabel(statusCode, stale, hasQuota, fetchedAtText, inFlight) {
        if (inFlight && (statusCode === "idle" || statusCode === ""))
            return "Loading…"
        if (statusCode === "ok")
            return ""
        if (statusCode === "stale" || (stale && hasQuota))
            return fetchedAtText ? ("Cached · " + fetchedAtText) : "Cached"
        if (statusCode === "auth_unavailable")
            return "Needs authentication"
        if (statusCode === "upstream_error")
            return hasQuota && fetchedAtText ? ("Unavailable · cached " + fetchedAtText) : "Unavailable"
        if (statusCode === "provider_unavailable")
            return "Provider unavailable"
        if (statusCode === "collector_error")
            return "Collector error"
        if (statusCode === "idle")
            return ""
        return "Unavailable"
    }

    function applyPayload(providerId, obj) {
        var idx = indexForProvider(providerId)
        if (idx < 0)
            return

        if (!obj || typeof obj !== "object") {
            providersModel.set(idx, {
                providerName: providerId,
                planName: "",
                remainingPercent: -1,
                secondaryRemainingPercent: -1,
                breakdownJson: "[]",
                resetText: "",
                statusCode: "collector_error",
                statusLabel: "Collector error",
                errorText: "",
                fetchedAtText: "",
                stale: false,
                hasQuota: false,
                inFlight: false
            })
            updateAnyInFlight()
            updateCompactSummary()
            return
        }

        var statusCode = obj.status || "collector_error"
        var stale = obj.stale === true || statusCode === "stale"
        var providerName = obj.displayName || obj.provider || providerId
        var planName = ""
        var remainingPercent = -1
        var secondaryRemainingPercent = -1
        var breakdownJson = "[]"
        var resetText = ""
        var fetchedAtText = ""
        var hasQuota = false

        if (statusCode === "ok" || statusCode === "stale") {
            planName = obj.plan || ""
            remainingPercent = (typeof obj.remainingPercent === "number") ? obj.remainingPercent : -1
            secondaryRemainingPercent = (typeof obj.secondaryRemainingPercent === "number")
                ? obj.secondaryRemainingPercent
                : -1
            if (Array.isArray(obj.breakdown)) {
                var lines = []
                for (var i = 0; i < obj.breakdown.length; i++) {
                    var line = obj.breakdown[i]
                    if (!line || typeof line !== "object")
                        continue
                    if (typeof line.remainingPercent !== "number")
                        continue
                    var lineReset = line.resetAt || obj.resetAt || ""
                    lines.push({
                        label: String(line.label || ""),
                        remainingPercent: line.remainingPercent,
                        resetText: formatRelative(lineReset)
                    })
                }
                breakdownJson = JSON.stringify(lines)
            } else if (remainingPercent >= 0) {
                var fallback = [{
                    label: "",
                    remainingPercent: remainingPercent,
                    resetText: formatRelative(obj.resetAt || "")
                }]
                if (secondaryRemainingPercent >= 0) {
                    fallback.push({
                        label: "Secondary",
                        remainingPercent: secondaryRemainingPercent,
                        resetText: formatRelative(obj.resetAt || "")
                    })
                }
                breakdownJson = JSON.stringify(fallback)
            }
            resetText = formatRelative(obj.resetAt)
            fetchedAtText = formatFetchedAt(obj.fetchedAt)
            hasQuota = remainingPercent >= 0 || (Array.isArray(obj.breakdown) && obj.breakdown.length > 0)
        }

        var statusLabel = friendlyStatusLabel(statusCode, stale, hasQuota, fetchedAtText, false)

        providersModel.set(idx, {
            providerName: providerName,
            planName: planName,
            remainingPercent: remainingPercent,
            secondaryRemainingPercent: secondaryRemainingPercent,
            breakdownJson: breakdownJson,
            resetText: resetText,
            statusCode: statusCode,
            statusLabel: statusLabel,
            errorText: "",
            fetchedAtText: fetchedAtText,
            stale: stale,
            hasQuota: hasQuota,
            inFlight: false
        })
        updateAnyInFlight()
        updateCompactSummary()
    }

    function lowestQuotaPercent() {
        var min = null
        for (var i = 0; i < providersModel.count; i++) {
            var row = providersModel.get(i)
            if (!row.hasQuota || typeof row.remainingPercent !== "number" || row.remainingPercent < 0)
                continue
            var candidate = row.remainingPercent
            try {
                var lines = JSON.parse(row.breakdownJson || "[]")
                for (var j = 0; j < lines.length; j++) {
                    if (typeof lines[j].remainingPercent === "number")
                        candidate = Math.min(candidate, lines[j].remainingPercent)
                }
            } catch (e) { }
            if (min === null || candidate < min)
                min = candidate
        }
        return min
    }

    function updateCompactSummary() {
        var min = lowestQuotaPercent()
        if (min === null) {
            var anyEnabled = enabledProviderIds().length > 0
            var anyAuth = false
            var anyErr = false
            for (var i = 0; i < providersModel.count; i++) {
                var st = providersModel.get(i).statusCode
                if (st === "auth_unavailable")
                    anyAuth = true
                if (st !== "idle" && st !== "ok")
                    anyErr = true
            }
            if (!anyEnabled)
                compactText = "AI"
            else if (anyAuth)
                compactText = "AI !"
            else if (anyErr)
                compactText = "AI —"
            else
                compactText = "AI …"
        } else {
            compactText = "AI " + min + "%"
        }

        var bits = []
        for (var k = 0; k < providersModel.count; k++) {
            var row = providersModel.get(k)
            var line = row.providerName
            if (row.hasQuota) {
                line += "  " + row.remainingPercent + "%"
                if (row.secondaryRemainingPercent >= 0)
                    line += " / " + row.secondaryRemainingPercent + "%"
                if (row.stale)
                    line += " (cached)"
            } else if (row.statusLabel) {
                line += "  " + row.statusLabel
            } else if (row.inFlight) {
                line += "  …"
            } else {
                line += "  —"
            }
            bits.push(line)
        }
        tooltipSummary = bits.length ? bits.join("\n") : "No providers enabled"
    }

    function updateAnyInFlight() {
        var busy = false
        for (var i = 0; i < providersModel.count; i++) {
            if (providersModel.get(i).inFlight) {
                busy = true
                break
            }
        }
        anyInFlight = busy
    }

    function refreshProvider(providerId) {
        if (!providerEnabled(providerId))
            return
        var idx = indexForProvider(providerId)
        if (idx < 0)
            return
        if (providersModel.get(idx).inFlight)
            return
        providersModel.setProperty(idx, "inFlight", true)
        if (providersModel.get(idx).statusCode === "idle")
            providersModel.setProperty(idx, "statusLabel", "Loading…")
        updateAnyInFlight()
        updateCompactSummary()
        executable.exec(collectorCommand(providerId))
    }

    function refreshUsage() {
        syncModelToEnabled()
        var ids = enabledProviderIds()
        if (ids.length === 0) {
            updateCompactSummary()
            return
        }
        for (var i = 0; i < ids.length; i++)
            refreshProvider(ids[i])
    }

    function onConfigChanged() {
        syncModelToEnabled()
        refreshTimer.restart()
        refreshUsage()
    }

    onExpandedChanged: function (expanded) {
        if (expanded)
            refreshUsage()
    }

    Connections {
        target: plasmoid.configuration
        function onEnableCodexChanged() { root.onConfigChanged() }
        function onEnableCursorChanged() { root.onConfigChanged() }
        function onEnableStepfunChanged() { root.onConfigChanged() }
        function onRefreshIntervalMinutesChanged() {
            refreshTimer.interval = Math.max(1, plasmoid.configuration.refreshIntervalMinutes) * 60 * 1000
            refreshTimer.restart()
        }
    }

    Timer {
        id: refreshTimer
        interval: Math.max(1, plasmoid.configuration.refreshIntervalMinutes) * 60 * 1000
        running: true
        repeat: true
        onTriggered: root.refreshUsage()
    }

    Component.onCompleted: {
        syncModelToEnabled()
        refreshUsage()
    }

    P5Support.DataSource {
        id: executable
        engine: "executable"
        connectedSources: []

        onNewData: function (sourceName, data) {
            var stdout = data["stdout"] ? String(data["stdout"]).trim() : ""
            var providerId = root.providerIdFromCommand(sourceName)
            disconnectSource(sourceName)

            if (!providerId || !root.providerEnabled(providerId))
                return

            if (!stdout) {
                root.applyPayload(providerId, {
                    provider: providerId,
                    displayName: providerId,
                    status: "collector_error"
                })
                return
            }

            try {
                root.applyPayload(providerId, JSON.parse(stdout))
            } catch (e) {
                root.applyPayload(providerId, {
                    provider: providerId,
                    displayName: providerId,
                    status: "collector_error"
                })
            }
        }

        function exec(cmd) {
            connectSource(cmd)
        }
    }

    compactRepresentation: MouseArea {
        Layout.minimumWidth: Kirigami.Units.gridUnit * 2
        Layout.minimumHeight: Kirigami.Units.gridUnit
        Layout.preferredWidth: compactLabel.implicitWidth + Kirigami.Units.smallSpacing * 2
        Layout.preferredHeight: Math.max(compactLabel.implicitHeight, Kirigami.Units.iconSizes.small)

        acceptedButtons: Qt.LeftButton
        onClicked: root.expanded = !root.expanded

        PlasmaComponents.Label {
            id: compactLabel
            anchors.centerIn: parent
            text: root.compactText
            font.bold: true
        }
    }

    fullRepresentation: Item {
        property int contentWidth: Kirigami.Units.gridUnit * 18
        property int contentHeight: Kirigami.Units.gridUnit * 36

        Layout.minimumWidth: contentWidth
        Layout.minimumHeight: contentHeight
        Layout.preferredWidth: contentWidth
        Layout.preferredHeight: contentHeight
        implicitWidth: contentWidth
        implicitHeight: contentHeight
        width: contentWidth
        height: contentHeight

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.smallSpacing

            PlasmaComponents.Label {
                Layout.fillWidth: true
                text: "Horizon"
                font.bold: true
                font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.2
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true
                text: "AI Agent Usage"
                opacity: 0.8
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true
                visible: providersModel.count === 0
                wrapMode: Text.WordWrap
                text: "No providers enabled. Open widget settings to enable Codex, Cursor, or StepFun."
                opacity: 0.85
            }

            Kirigami.Separator {
                Layout.fillWidth: true
                Layout.topMargin: Kirigami.Units.smallSpacing
                Layout.bottomMargin: Kirigami.Units.smallSpacing
                visible: providersModel.count > 0
            }

            Repeater {
                model: providersModel

                delegate: ColumnLayout {
                    id: providerBlock
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing

                    readonly property var usageLines: {
                        try {
                            return JSON.parse(model.breakdownJson || "[]")
                        } catch (e) {
                            return []
                        }
                    }

                    readonly property bool hasPerLineReset: {
                        var lines = providerBlock.usageLines
                        for (var i = 0; i < lines.length; i++) {
                            if (lines[i].resetText && String(lines[i].resetText).length > 0)
                                return true
                        }
                        return false
                    }

                    PlasmaComponents.Label {
                        Layout.fillWidth: true
                        text: model.providerName
                        font.bold: true
                    }

                    PlasmaComponents.Label {
                        Layout.fillWidth: true
                        visible: model.hasQuota && model.planName.length > 0
                        text: model.planName
                        opacity: 0.85
                    }

                    Repeater {
                        model: providerBlock.usageLines
                        delegate: ColumnLayout {
                            Layout.fillWidth: true
                            spacing: Kirigami.Units.smallSpacing / 2
                            visible: modelData.remainingPercent >= 0

                            PlasmaComponents.Label {
                                Layout.fillWidth: true
                                visible: String(modelData.label || "").length > 0
                                text: modelData.label
                                opacity: 0.75
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: Kirigami.Units.smallSpacing

                                PlasmaComponents.Label {
                                    text: modelData.remainingPercent + "%"
                                    font.bold: true
                                }

                                PlasmaComponents.ProgressBar {
                                    Layout.fillWidth: true
                                    from: 0
                                    to: 100
                                    value: Math.max(0, modelData.remainingPercent)
                                    indeterminate: false
                                }
                            }

                            PlasmaComponents.Label {
                                Layout.fillWidth: true
                                visible: String(modelData.resetText || "").length > 0
                                text: "Reset: " + modelData.resetText
                                opacity: 0.85
                            }
                        }
                    }

                    PlasmaComponents.Label {
                        Layout.fillWidth: true
                        visible: model.hasQuota && model.resetText.length > 0 && !providerBlock.hasPerLineReset
                        text: "Reset: " + model.resetText
                        opacity: 0.85
                    }

                    PlasmaComponents.Label {
                        Layout.fillWidth: true
                        visible: model.statusLabel.length > 0
                        wrapMode: Text.WordWrap
                        text: model.statusLabel
                        color: (model.statusCode === "ok")
                            ? Kirigami.Theme.textColor
                            : (model.stale ? Kirigami.Theme.neutralTextColor : Kirigami.Theme.negativeTextColor)
                    }

                    Kirigami.Separator {
                        Layout.fillWidth: true
                        Layout.topMargin: Kirigami.Units.smallSpacing
                        Layout.bottomMargin: Kirigami.Units.smallSpacing
                        visible: index < providersModel.count - 1
                    }
                }
            }

            Item {
                Layout.fillHeight: true
                Layout.minimumHeight: Kirigami.Units.smallSpacing
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing

                PlasmaComponents.Button {
                    text: root.anyInFlight ? "Refreshing…" : "Refresh"
                    enabled: providersModel.count > 0
                    onClicked: root.refreshUsage()
                }

                PlasmaComponents.Label {
                    Layout.fillWidth: true
                    text: root.anyInFlight ? "Updating…" : ""
                    opacity: 0.7
                    elide: Text.ElideRight
                }
            }
        }
    }
}
