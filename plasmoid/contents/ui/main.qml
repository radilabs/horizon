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
    toolTipSubText: root.compactSummary

    preferredRepresentation: Plasmoid.formFactor === PlasmaCore.Types.Planar
        ? fullRepresentation
        : compactRepresentation

    switchWidth: Kirigami.Units.gridUnit * 12
    switchHeight: Kirigami.Units.gridUnit * 8
    activationTogglesExpanded: true

    // Phase 3: explicit fixed provider list (no settings / discovery).
    readonly property var providerIds: ["codex", "cursor", "stepfun"]

    property int pendingCount: 0
    property bool loading: pendingCount > 0
    property string compactSummary: "AI Agent Usage"

    ListModel {
        id: providersModel
    }

    function filesystemPath(urlOrPath) {
        var s = String(urlOrPath)
        if (s.indexOf("file://") === 0)
            return decodeURIComponent(s.substring(7))
        return s
    }

    function collectorCommand(providerId) {
        var home = filesystemPath(StandardPaths.writableLocation(StandardPaths.HomeLocation))
        return home + "/.local/bin/ai-usage status " + providerId + " --json"
    }

    function providerIdFromCommand(cmd) {
        // Expect: …/ai-usage status <id> --json
        var parts = String(cmd).trim().split(/\s+/)
        var statusIdx = parts.indexOf("status")
        if (statusIdx >= 0 && statusIdx + 1 < parts.length)
            return parts[statusIdx + 1]
        return ""
    }

    function ensureModel() {
        if (providersModel.count === providerIds.length)
            return
        providersModel.clear()
        for (var i = 0; i < providerIds.length; i++) {
            providersModel.append({
                providerId: providerIds[i],
                providerName: providerIds[i],
                planName: "",
                remainingPercent: -1,
                secondaryRemainingPercent: -1,
                breakdownJson: "[]",
                resetText: "",
                statusCode: "idle",
                errorText: "",
                fetchedAtText: "",
                stale: false,
                hasQuota: false
            })
        }
    }

    function indexForProvider(providerId) {
        for (var i = 0; i < providersModel.count; i++) {
            if (providersModel.get(i).providerId === providerId)
                return i
        }
        return -1
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
                errorText: "Malformed collector output",
                fetchedAtText: "",
                stale: false,
                hasQuota: false
            })
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
        var errorText = ""
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
                // Synthetic single/dual lines when provider has no labeled breakdown.
                var fallback = [{
                    label: "",
                    remainingPercent: remainingPercent,
                    resetText: formatRelative(obj.resetAt || "")
                }]
                if (secondaryRemainingPercent >= 0)
                    fallback.push({
                        label: "Secondary",
                        remainingPercent: secondaryRemainingPercent,
                        resetText: formatRelative(obj.resetAt || "")
                    })
                breakdownJson = JSON.stringify(fallback)
            }
            resetText = formatRelative(obj.resetAt)
            fetchedAtText = formatFetchedAt(obj.fetchedAt)
            errorText = stale ? (obj.error || "Refresh failed") : ""
            hasQuota = remainingPercent >= 0 || (Array.isArray(obj.breakdown) && obj.breakdown.length > 0)
        } else {
            errorText = obj.error || statusCode
        }

        providersModel.set(idx, {
            providerName: providerName,
            planName: planName,
            remainingPercent: remainingPercent,
            secondaryRemainingPercent: secondaryRemainingPercent,
            breakdownJson: breakdownJson,
            resetText: resetText,
            statusCode: statusCode,
            errorText: errorText,
            fetchedAtText: fetchedAtText,
            stale: stale,
            hasQuota: hasQuota
        })
        updateCompactSummary()
    }

    function updateCompactSummary() {
        var bits = []
        for (var i = 0; i < providersModel.count; i++) {
            var row = providersModel.get(i)
            if (row.hasQuota)
                bits.push(row.providerName + " " + row.remainingPercent + "%" + (row.stale ? "*" : ""))
        }
        compactSummary = bits.length ? bits.join(" · ") : "AI Agent Usage"
    }

    function refreshUsage() {
        if (loading)
            return
        ensureModel()
        pendingCount = providerIds.length
        for (var i = 0; i < providerIds.length; i++)
            executable.exec(collectorCommand(providerIds[i]))
    }

    onExpandedChanged: function (expanded) {
        if (expanded)
            refreshUsage()
    }

    Component.onCompleted: {
        ensureModel()
        refreshUsage()
    }

    P5Support.DataSource {
        id: executable
        engine: "executable"
        connectedSources: []

        onNewData: function (sourceName, data) {
            var stdout = data["stdout"] ? String(data["stdout"]).trim() : ""
            var stderr = data["stderr"] ? String(data["stderr"]).trim() : ""
            var providerId = root.providerIdFromCommand(sourceName)
            disconnectSource(sourceName)
            if (root.pendingCount > 0)
                root.pendingCount -= 1

            if (!providerId) {
                return
            }

            if (!stdout) {
                root.applyPayload(providerId, {
                    provider: providerId,
                    displayName: providerId,
                    status: "collector_error",
                    error: stderr || "Collector produced no output"
                })
                return
            }

            try {
                root.applyPayload(providerId, JSON.parse(stdout))
            } catch (e) {
                root.applyPayload(providerId, {
                    provider: providerId,
                    displayName: providerId,
                    status: "collector_error",
                    error: "Malformed collector output"
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
            text: "AI"
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

            Kirigami.Separator {
                Layout.fillWidth: true
                Layout.topMargin: Kirigami.Units.smallSpacing
                Layout.bottomMargin: Kirigami.Units.smallSpacing
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
                        visible: model.hasQuota
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
                        visible: model.stale && model.hasQuota
                        wrapMode: Text.WordWrap
                        text: "Cached" + (model.fetchedAtText.length ? (" — updated " + model.fetchedAtText) : "")
                        color: Kirigami.Theme.neutralTextColor
                    }

                    PlasmaComponents.Label {
                        Layout.fillWidth: true
                        visible: model.stale && model.errorText.length > 0
                        wrapMode: Text.WordWrap
                        text: model.errorText
                        color: Kirigami.Theme.negativeTextColor
                    }

                    PlasmaComponents.Label {
                        Layout.fillWidth: true
                        visible: !model.hasQuota
                        wrapMode: Text.WordWrap
                        text: root.loading && model.statusCode === "idle"
                            ? "Loading usage…"
                            : (model.errorText.length ? model.errorText : "Usage unavailable")
                        color: (root.loading && model.statusCode === "idle")
                            ? Kirigami.Theme.textColor
                            : Kirigami.Theme.negativeTextColor
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
                    text: root.loading ? "Refreshing…" : "Refresh"
                    enabled: !root.loading
                    onClicked: root.refreshUsage()
                }

                PlasmaComponents.Label {
                    Layout.fillWidth: true
                    text: root.loading ? "Running ai-usage…" : ""
                    opacity: 0.7
                    elide: Text.ElideRight
                }
            }
        }
    }
}
