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

    property string providerName: "Codex"
    property string planName: ""
    property int remainingPercent: -1
    property string resetText: ""
    property string statusCode: "idle"
    property string statusText: "AI Agent Usage"
    property string errorText: ""
    property bool loading: false
    property bool hasData: remainingPercent >= 0 && statusCode === "ok"

    function filesystemPath(urlOrPath) {
        var s = String(urlOrPath)
        if (s.indexOf("file://") === 0)
            return decodeURIComponent(s.substring(7))
        return s
    }

    function collectorCommand() {
        var home = filesystemPath(StandardPaths.writableLocation(StandardPaths.HomeLocation))
        return home + "/.local/bin/ai-usage status codex --json"
    }

    function formatReset(iso) {
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

    function applyPayload(obj) {
        if (!obj || typeof obj !== "object") {
            statusCode = "collector_error"
            errorText = "Malformed collector output"
            planName = ""
            remainingPercent = -1
            resetText = ""
            statusText = "Collector error"
            return
        }
        providerName = obj.displayName || obj.provider || "Codex"
        statusCode = obj.status || "collector_error"
        if (statusCode === "ok") {
            planName = obj.plan || ""
            remainingPercent = (typeof obj.remainingPercent === "number") ? obj.remainingPercent : -1
            resetText = formatReset(obj.resetAt)
            errorText = ""
            statusText = providerName + (remainingPercent >= 0 ? (" " + remainingPercent + "%") : "")
        } else {
            planName = ""
            remainingPercent = -1
            resetText = ""
            errorText = obj.error || statusCode
            statusText = "Codex unavailable"
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

    Component.onCompleted: {
        // Prefetch so first open is faster when possible.
        refreshUsage()
    }

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
                planName = ""
                remainingPercent = -1
                resetText = ""
                statusText = "Collector error"
                return
            }

            try {
                var obj = JSON.parse(stdout)
                applyPayload(obj)
            } catch (e) {
                statusCode = "collector_error"
                errorText = "Malformed collector output"
                planName = ""
                remainingPercent = -1
                resetText = ""
                statusText = "Collector error"
            }
        }

        function exec(cmd) {
            connectSource(cmd)
        }
    }

    compactRepresentation: MouseArea {
        id: compactRoot

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
        id: fullRoot

        property int contentWidth: Kirigami.Units.gridUnit * 18
        property int contentHeight: Kirigami.Units.gridUnit * 14

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
                text: root.providerName
                font.bold: true
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true
                visible: root.hasData
                text: root.planName
                opacity: 0.85
            }

            RowLayout {
                Layout.fillWidth: true
                visible: root.hasData
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
                visible: root.hasData && root.resetText.length > 0
                text: "Reset: " + root.resetText
                opacity: 0.85
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true
                visible: !root.hasData
                wrapMode: Text.WordWrap
                text: root.loading
                    ? "Loading Codex usage…"
                    : (root.errorText.length ? root.errorText : "Codex usage unavailable")
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
                    text: root.loading ? "Running ai-usage…" : (root.hasData ? "" : root.statusCode)
                    opacity: 0.7
                    elide: Text.ElideRight
                }
            }
        }
    }
}
