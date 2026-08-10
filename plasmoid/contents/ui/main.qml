import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    Plasmoid.title: "Horizon"
    toolTipMainText: "Horizon"
    toolTipSubText: "AI Agent Usage"

    // Prefer compact on panels; full representation is the popup content.
    preferredRepresentation: Plasmoid.formFactor === PlasmaCore.Types.Planar
        ? fullRepresentation
        : compactRepresentation

    switchWidth: Kirigami.Units.gridUnit * 12
    switchHeight: Kirigami.Units.gridUnit * 8
    activationTogglesExpanded: true

    // Phase 0 fake Codex usage — hardcoded, no network/auth/collector.
    property string providerName: "Codex"
    property string planName: "ChatGPT Plus"
    property int remainingPercent: 72
    property string resetText: "2h 14m"
    property string refreshStatus: ""

    function refreshFakeData() {
        // Harmless local action for Phase 0 refresh control.
        refreshStatus = "Refreshed (fake)"
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

        // Explicit sizes so the panel popup is large enough to show fake Codex fields.
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
                text: root.planName
                opacity: 0.85
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing

                PlasmaComponents.Label {
                    text: root.remainingPercent + "%"
                    font.bold: true
                }

                PlasmaComponents.ProgressBar {
                    Layout.fillWidth: true
                    from: 0
                    to: 100
                    value: root.remainingPercent
                    indeterminate: false
                }
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true
                text: "Reset: " + root.resetText
                opacity: 0.85
            }

            Item {
                Layout.fillHeight: true
                Layout.minimumHeight: Kirigami.Units.smallSpacing
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing

                PlasmaComponents.Button {
                    text: "Refresh"
                    onClicked: root.refreshFakeData()
                }

                PlasmaComponents.Label {
                    Layout.fillWidth: true
                    text: root.refreshStatus
                    opacity: 0.7
                    elide: Text.ElideRight
                }
            }
        }
    }
}
