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
    toolTipSubText: root.statusText

    preferredRepresentation: Plasmoid.formFactor === PlasmaCore.Types.Planar
        ? fullRepresentation
        : compactRepresentation

    switchWidth: Kirigami.Units.gridUnit * 12
    switchHeight: Kirigami.Units.gridUnit * 8
    activationTogglesExpanded: true

    // Phase 2: single configured provider id for the collector command.
    // Display names come from normalized JSON, not hard-coded product copy.
    property string configuredProvider: "codex"

    property string providerName: ""
    property string planName: ""
    property int remainingPercent: -1
    property string resetText: ""
    property string statusCode: "idle"
    property string statusText: "AI Agent Usage"
    property string errorText: ""
    property string fetchedAtText: ""
    property bool stale: false
    property bool loading: false
    property bool hasQuota: remainingPercent >= 0 && (statusCode === "ok" || statusCode === "stale")

    function filesystemPath(urlOrPath) {
        var s = String(urlOrPath)
        if (s.indexOf("file://") === 0)
            return decodeURIComponent(s.substring(7))
        return s
    }

    function collectorCommand() {
        var home = filesystemPath(StandardPaths.writableLocation(StandardPaths.HomeLocation))
        return home + "/.local/bin/ai-usage status " + configuredProvider + " --json"
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

    function applyPayload(obj) {
        if (!obj || typeof obj !== "object") {
            statusCode = "collector_error"
            errorText = "Malformed collector output"
            providerName = ""
            planName = ""
            remainingPercent = -1
            resetText = ""
            fetchedAtText = ""
            stale = false
            statusText = "Collector error"
            return
        }

        providerName = obj.displayName || obj.provider || configuredProvider
        statusCode = obj.status || "collector_error"
        stale = obj.stale === true || statusCode === "stale"

        if (statusCode === "ok" || statusCode === "stale") {
            planName = obj.plan || ""
            remainingPercent = (typeof obj.remainingPercent === "number") ? obj.remainingPercent : -1
            resetText = formatRelative(obj.resetAt)
            fetchedAtText = formatFetchedAt(obj.fetchedAt)
            errorText = stale ? (obj.error || "Refresh failed") : ""
            statusText = providerName + (remainingPercent >= 0 ? (" " + remainingPercent + "%") : "")
            if (stale)
                statusText += " (cached)"
        } else {
            planName = ""
            remainingPercent = -1
            resetText = ""
            fetchedAtText = ""
            errorText = obj.error || statusCode
            statusText = "Usage unavailable"
        }
    }

    function refreshUsage() {
        if (loading)
            return
        loading = true
        errorText = ""
        executable.exec(collectorCommand())
    }

    onExpandedChanged: function (expanded) {
        if (expanded)
            refreshUsage()
    }

    Component.onCompleted: refreshUsage()

    P5Support.DataSource {
        id: executable
        engine: "executable"
        connectedSources: []

        onNewData: function (sourceName, data) {
            var stdout = data["stdout"] ? String(data["stdout"]).trim() : ""
            var stderr = data["stderr"] ? String(data["stderr"]).trim() : ""
            disconnectSource(sourceName)
            loading = false

            if (!stdout) {
                statusCode = "collector_error"
                errorText = stderr || "Collector produced no output"
                providerName = ""
                planName = ""
                remainingPercent = -1
                resetText = ""
                fetchedAtText = ""
                stale = false
                statusText = "Collector error"
                return
            }

            try {
                applyPayload(JSON.parse(stdout))
            } catch (e) {
                statusCode = "collector_error"
                errorText = "Malformed collector output"
                providerName = ""
                planName = ""
                remainingPercent = -1
                resetText = ""
                fetchedAtText = ""
                stale = false
                statusText = "Collector error"
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
        property int contentHeight: Kirigami.Units.gridUnit * 15

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

            PlasmaComponents.Label {
                Layout.fillWidth: true
                text: root.providerName.length ? root.providerName : root.configuredProvider
                font.bold: true
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true
                visible: root.hasQuota
                text: root.planName
                opacity: 0.85
            }

            RowLayout {
                Layout.fillWidth: true
                visible: root.hasQuota
                spacing: Kirigami.Units.smallSpacing

                PlasmaComponents.Label {
                    text: root.remainingPercent + "%"
                    font.bold: true
                }

                PlasmaComponents.ProgressBar {
                    Layout.fillWidth: true
                    from: 0
                    to: 100
                    value: Math.max(0, root.remainingPercent)
                    indeterminate: false
                }
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true
                visible: root.hasQuota && root.resetText.length > 0
                text: "Reset: " + root.resetText
                opacity: 0.85
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true
                visible: root.stale && root.hasQuota
                wrapMode: Text.WordWrap
                text: "Cached" + (root.fetchedAtText.length ? (" — updated " + root.fetchedAtText) : "")
                color: Kirigami.Theme.neutralTextColor
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true
                visible: root.stale && root.errorText.length > 0
                wrapMode: Text.WordWrap
                text: root.errorText
                color: Kirigami.Theme.negativeTextColor
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true
                visible: !root.hasQuota
                wrapMode: Text.WordWrap
                text: root.loading
                    ? "Loading usage…"
                    : (root.errorText.length ? root.errorText : "Usage unavailable")
                color: root.loading ? Kirigami.Theme.textColor : Kirigami.Theme.negativeTextColor
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
                    text: root.loading ? "Running ai-usage…" : (root.hasQuota && !root.stale ? "" : root.statusCode)
                    opacity: 0.7
                    elide: Text.ElideRight
                }
            }
        }
    }
}
