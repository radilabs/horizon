import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import QtQuick.Window
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
    toolTipTextFormat: Text.PlainText
    // Plasma's default tooltip label stops at 8 lines, which hides later providers.
    toolTipItem: Item {
        implicitWidth: tipColumn.implicitWidth + Kirigami.Units.largeSpacing * 2
        implicitHeight: tipColumn.implicitHeight + Kirigami.Units.largeSpacing * 2

        Column {
            id: tipColumn
            x: Kirigami.Units.largeSpacing
            y: Kirigami.Units.largeSpacing
            spacing: 0

            Kirigami.Heading {
                level: 3
                text: "Horizon"
            }

            PlasmaComponents.Label {
                text: root.tooltipSummary
                textFormat: Text.PlainText
                wrapMode: Text.NoWrap
                color: Kirigami.Theme.textColor
            }
        }
    }

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
                metersJson: row.metersJson || "[]",
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
                    metersJson: "[]",
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
                providerId: providerId,
                providerName: providerId,
                planName: "",
                metersJson: "[]",
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
        var metersJson = "[]"
        var fetchedAtText = ""
        var hasQuota = false

        if (statusCode === "ok" || statusCode === "stale") {
            planName = obj.plan || ""
            fetchedAtText = formatFetchedAt(obj.fetchedAt)
            metersJson = popupMetersJson(obj)
            try {
                hasQuota = JSON.parse(metersJson).length > 0
            } catch (e) {
                hasQuota = false
            }
        }

        var statusLabel = friendlyStatusLabel(statusCode, stale, hasQuota, fetchedAtText, false)
        var errorText = (obj && typeof obj.error === "string") ? obj.error : ""

        providersModel.set(idx, {
            providerId: providerId,
            providerName: providerName,
            planName: planName,
            metersJson: metersJson,
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

    function providerSnapshots() {
        var list = []
        for (var i = 0; i < providersModel.count; i++) {
            var row = providersModel.get(i)
            var meters = []
            try {
                meters = JSON.parse(row.metersJson || "[]")
            } catch (e) {
                meters = []
            }
            list.push({
                name: row.providerName,
                plan: row.planName,
                statusCode: row.statusCode,
                statusLabel: row.statusLabel,
                errorText: row.errorText,
                stale: row.stale,
                fetchedAtText: row.fetchedAtText,
                inFlight: row.inFlight,
                meters: meters
            })
        }
        return list
    }

    function updateCompactSummary() {
        var providers = providerSnapshots()
        compactText = MeterIntake.compactText(providers)
        tooltipSummary = MeterIntake.tooltipText(providers)
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
        readonly property bool verticalPanel: Plasmoid.formFactor === PlasmaCore.Types.Vertical
        readonly property int textWidth: compactLabel.implicitWidth + Kirigami.Units.smallSpacing * 2

        Layout.minimumWidth: Kirigami.Units.gridUnit * 2
        Layout.minimumHeight: Kirigami.Units.gridUnit
        Layout.preferredWidth: verticalPanel
            ? Math.min(textWidth, Kirigami.Units.gridUnit * 6)
            : textWidth
        Layout.maximumWidth: verticalPanel ? Kirigami.Units.gridUnit * 6 : textWidth
        Layout.preferredHeight: Math.max(compactLabel.implicitHeight, Kirigami.Units.iconSizes.small)

        acceptedButtons: Qt.LeftButton
        onClicked: root.expanded = !root.expanded

        PlasmaComponents.Label {
            id: compactLabel
            anchors.fill: parent
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            text: root.compactText
            font.bold: true
            elide: Text.ElideRight
        }
    }

    fullRepresentation: Item {
        id: popup
        readonly property int availableScreenHeight: Screen.desktopAvailableHeight > 0
            ? Screen.desktopAvailableHeight
            : Screen.height
        readonly property int maxPopupHeight: Math.min(
            Kirigami.Units.gridUnit * 40,
            Math.max(Kirigami.Units.gridUnit * 12, Math.round(availableScreenHeight * 0.8))
        )
        readonly property int chromeHeight: Kirigami.Units.largeSpacing * 2
            + Kirigami.Units.smallSpacing * 2
            + headerRow.implicitHeight
            + subtitleLabel.implicitHeight
        readonly property int listHeight: Math.max(providerColumn.implicitHeight, providerColumn.childrenRect.height)
        readonly property int contentHeight: chromeHeight + listHeight + Kirigami.Units.largeSpacing

        implicitWidth: Kirigami.Units.gridUnit * 20
        implicitHeight: Math.max(Kirigami.Units.gridUnit * 12, Math.min(contentHeight, maxPopupHeight))
        Layout.minimumWidth: Kirigami.Units.gridUnit * 16
        Layout.minimumHeight: Kirigami.Units.gridUnit * 12
        Layout.preferredWidth: implicitWidth
        Layout.preferredHeight: implicitHeight
        Layout.maximumHeight: maxPopupHeight

        Shortcut {
            sequences: ["F5"]
            context: Qt.WindowShortcut
            enabled: providersModel.count > 0
            onActivated: root.refreshUsage()
        }

        ColumnLayout {
            id: popupColumn
            anchors.fill: parent
            anchors.margins: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.smallSpacing

            RowLayout {
                id: headerRow
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing

                Kirigami.Heading {
                    Layout.fillWidth: true
                    level: 4
                    text: "Horizon"
                }

                QQC2.BusyIndicator {
                    visible: root.anyInFlight
                    running: root.anyInFlight
                    Layout.preferredWidth: Kirigami.Units.iconSizes.small
                    Layout.preferredHeight: Kirigami.Units.iconSizes.small
                }

                PlasmaComponents.ToolButton {
                    id: refreshButton
                    icon.name: "view-refresh"
                    text: "Refresh"
                    display: QQC2.AbstractButton.IconOnly
                    enabled: providersModel.count > 0
                    activeFocusOnTab: true
                    Accessible.name: root.anyInFlight ? "Refreshing" : "Refresh"
                    Accessible.description: "Refresh usage for every enabled provider"
                    onClicked: root.refreshUsage()
                    Keys.onReturnPressed: if (enabled) root.refreshUsage()
                    Keys.onEnterPressed: if (enabled) root.refreshUsage()
                    Keys.onSpacePressed: if (enabled) root.refreshUsage()

                    QQC2.ToolTip.visible: hovered || activeFocus
                    QQC2.ToolTip.text: root.anyInFlight ? "Refreshing…" : "Refresh"
                    QQC2.ToolTip.delay: Kirigami.Units.shortDuration
                }
            }

            PlasmaComponents.Label {
                id: subtitleLabel
                Layout.fillWidth: true
                text: "AI Agent Usage"
                color: Kirigami.Theme.disabledTextColor
            }

            QQC2.ScrollView {
                id: scroller
                Layout.fillWidth: true
                Layout.fillHeight: true
                implicitHeight: popup.listHeight
                contentWidth: availableWidth

                Column {
                    id: providerColumn
                    width: scroller.availableWidth
                    spacing: Kirigami.Units.mediumSpacing

                    PlasmaComponents.Label {
                        width: parent.width
                        visible: providersModel.count === 0
                        wrapMode: Text.WordWrap
                        text: "No providers enabled. Open widget settings to enable Codex, Cursor, StepFun, or Claude."
                        color: Kirigami.Theme.disabledTextColor
                    }

                    Repeater {
                        model: providersModel

                        delegate: ColumnLayout {
                            id: providerBlock
                            width: providerColumn.width
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
                                            color: modelData.remainingPercent === 0
                                                ? Kirigami.Theme.negativeTextColor
                                                : Kirigami.Theme.textColor
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
                                color: (model.statusCode === "idle" || model.statusCode === "")
                                     ? Kirigami.Theme.disabledTextColor
                                     : (model.stale ? Kirigami.Theme.neutralTextColor
                                        : (model.statusCode === "ok" ? Kirigami.Theme.textColor
                                                                     : Kirigami.Theme.negativeTextColor))
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

        }
    }
}
