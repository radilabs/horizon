import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import QtCore
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import "MeterIntake.js" as MeterIntake

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

    readonly property var allProviderIds: ["codex", "cursor", "stepfun", "claude"]

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
        if (plasmoid.configuration.enableClaude)
            ids.push("claude")
        return ids
    }

    function providerEnabled(providerId) {
        if (providerId === "codex")
            return plasmoid.configuration.enableCodex
        if (providerId === "cursor")
            return plasmoid.configuration.enableCursor
        if (providerId === "stepfun")
            return plasmoid.configuration.enableStepfun
        if (providerId === "claude")
            return plasmoid.configuration.enableClaude
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
                metersJson: row.metersJson || "[]",
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
                    metersJson: "[]",
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

    function popupMetersJson(obj) {
        var rows = MeterIntake.intakeMeters(obj)
        var lines = []
        for (var i = 0; i < rows.length; i++) {
            lines.push({
                label: rows[i].label,
                remainingPercent: rows[i].remainingPercent,
                resetText: formatRelative(rows[i].resetAt || "")
            })
        }
        return JSON.stringify(lines)
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
                metersJson: "[]",
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
        var metersJson = "[]"
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
                        label: "Usage limit",
                        remainingPercent: secondaryRemainingPercent,
                        resetText: formatRelative(obj.resetAt || "")
                    })
                }
                breakdownJson = JSON.stringify(fallback)
            }
            resetText = formatRelative(obj.resetAt)
            fetchedAtText = formatFetchedAt(obj.fetchedAt)
            hasQuota = remainingPercent >= 0 || (Array.isArray(obj.breakdown) && obj.breakdown.length > 0)
            metersJson = popupMetersJson(obj)
        }

        var statusLabel = friendlyStatusLabel(statusCode, stale, hasQuota, fetchedAtText, false)
        var errorText = (obj && typeof obj.error === "string") ? obj.error : ""

        providersModel.set(idx, {
            providerName: providerName,
            planName: planName,
            remainingPercent: remainingPercent,
            secondaryRemainingPercent: secondaryRemainingPercent,
            breakdownJson: breakdownJson,
            metersJson: metersJson,
            resetText: resetText,
            statusCode: statusCode,
            statusLabel: statusLabel,
            errorText: errorText,
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
        function onEnableClaudeChanged() { root.onConfigChanged() }
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
        id: popup
        implicitWidth: Kirigami.Units.gridUnit * 20
        implicitHeight: Kirigami.Units.gridUnit * 32
        Layout.minimumWidth: Kirigami.Units.gridUnit * 16
        Layout.minimumHeight: Kirigami.Units.gridUnit * 16
        Layout.preferredWidth: implicitWidth
        Layout.preferredHeight: implicitHeight
        Layout.maximumHeight: Kirigami.Units.gridUnit * 36

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.smallSpacing

            Kirigami.Heading {
                Layout.fillWidth: true
                level: 4
                text: "Horizon"
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true
                text: "AI Agent Usage"
                color: Kirigami.Theme.disabledTextColor
            }

            QQC2.ScrollView {
                id: scroller
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: availableWidth

                ColumnLayout {
                    width: scroller.availableWidth
                    spacing: Kirigami.Units.mediumSpacing

                    PlasmaComponents.Label {
                        Layout.fillWidth: true
                        visible: providersModel.count === 0
                        wrapMode: Text.WordWrap
                        text: "No providers enabled. Open widget settings to enable Codex, Cursor, StepFun, or Claude."
                        color: Kirigami.Theme.disabledTextColor
                    }

                    Repeater {
                        model: providersModel

                        delegate: ColumnLayout {
                            id: providerBlock
                            Layout.fillWidth: true
                            spacing: Kirigami.Units.smallSpacing

                            readonly property bool showMeters: (model.statusCode === "ok" || model.statusCode === "stale") && model.hasQuota
                            readonly property var usageLines: {
                                if (!providerBlock.showMeters)
                                    return []
                                try {
                                    return JSON.parse(model.metersJson || "[]")
                                } catch (e) {
                                    return []
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: Kirigami.Units.smallSpacing

                                PlasmaComponents.Label {
                                    Layout.fillWidth: true
                                    text: model.providerName
                                    font.bold: true
                                    elide: Text.ElideRight
                                }

                                PlasmaComponents.Label {
                                    visible: model.planName.length > 0
                                    text: model.planName
                                    color: Kirigami.Theme.disabledTextColor
                                }
                            }

                            Repeater {
                                model: providerBlock.usageLines
                                delegate: ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: Kirigami.Units.smallSpacing / 2
                                    visible: modelData.remainingPercent >= 0

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: Kirigami.Units.smallSpacing

                                        PlasmaComponents.Label {
                                            Layout.fillWidth: true
                                            visible: String(modelData.label || "").length > 0
                                            text: modelData.label
                                            elide: Text.ElideRight
                                            color: Kirigami.Theme.textColor
                                        }

                                        PlasmaComponents.Label {
                                            text: modelData.remainingPercent + "% remaining"
                                            font.bold: true
                                        }
                                    }

                                    PlasmaComponents.ProgressBar {
                                        Layout.fillWidth: true
                                        from: 0
                                        to: 100
                                        value: Math.max(0, Math.min(100, modelData.remainingPercent))
                                        indeterminate: false
                                    }

                                    PlasmaComponents.Label {
                                        Layout.fillWidth: true
                                        visible: String(modelData.resetText || "").length > 0
                                        horizontalAlignment: Text.AlignRight
                                        text: "Resets in " + modelData.resetText
                                        color: Kirigami.Theme.disabledTextColor
                                    }
                                }
                            }

                            PlasmaComponents.Label {
                                Layout.fillWidth: true
                                visible: model.statusLabel.length > 0
                                wrapMode: Text.WordWrap
                                text: model.statusLabel
                                color: model.stale ? Kirigami.Theme.neutralTextColor
                                     : (model.statusCode === "ok" ? Kirigami.Theme.textColor
                                                                  : Kirigami.Theme.negativeTextColor)
                            }

                            PlasmaComponents.Label {
                                Layout.fillWidth: true
                                visible: model.errorText.length > 0
                                wrapMode: Text.WordWrap
                                text: model.errorText
                                color: Kirigami.Theme.negativeTextColor
                            }

                            Kirigami.Separator {
                                Layout.fillWidth: true
                                visible: index < providersModel.count - 1
                            }
                        }
                    }
                }
            }

            Kirigami.Separator {
                Layout.fillWidth: true
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
                    color: Kirigami.Theme.disabledTextColor
                    elide: Text.ElideRight
                }
            }
        }
    }
}
