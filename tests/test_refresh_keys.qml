import QtQuick
import org.kde.plasma.components as PlasmaComponents
import QtTest

Item {
    id: harness
    width: 240
    height: 80

    property int activations: 0
    property int manualActivations: 0
    property int providers: 2
    property bool busy: false

    function refresh(manual) {
        if (providers <= 0)
            return
        busy = true
        activations += 1
        if (manual === true)
            manualActivations += 1
    }

    PlasmaComponents.ToolButton {
        id: refreshButton
        width: 80
        height: 32
        text: "Refresh"
        focus: true
        enabled: harness.providers > 0
        Accessible.name: harness.busy ? "Refreshing" : "Refresh"
        onClicked: harness.refresh(true)
        Keys.onReturnPressed: function (event) {
            if (enabled) {
                event.accepted = true
                harness.refresh(true)
            }
        }
        Keys.onEnterPressed: function (event) {
            if (enabled) {
                event.accepted = true
                harness.refresh(true)
            }
        }
    }

    Shortcut {
        sequences: ["F5"]
        context: Qt.WindowShortcut
        enabled: harness.providers > 0
        onActivated: harness.refresh(true)
    }

    TestCase {
        name: "RefreshKeys"
        when: windowShown

        function init() {
            harness.activations = 0
            harness.manualActivations = 0
            harness.busy = false
            harness.providers = 2
            refreshButton.forceActiveFocus()
        }

        function test_click_activates_once_manual() {
            mouseClick(refreshButton, refreshButton.width / 2, refreshButton.height / 2, Qt.LeftButton)
            compare(harness.activations, 1)
            compare(harness.manualActivations, 1)
            compare(harness.busy, true)
        }

        function test_f5_refreshes() {
            keyClick(Qt.Key_F5)
            compare(harness.activations, 1)
            compare(harness.manualActivations, 1)
            compare(harness.busy, true)
            compare(refreshButton.Accessible.name, "Refreshing")
        }

        function test_space_activates_once() {
            keyClick(Qt.Key_Space)
            compare(harness.activations, 1)
            compare(harness.manualActivations, 1)
            compare(harness.busy, true)
        }

        function test_return_activates_once() {
            keyClick(Qt.Key_Return)
            compare(harness.activations, 1)
            compare(harness.manualActivations, 1)
            compare(harness.busy, true)
        }

        function test_enter_activates_once() {
            keyClick(Qt.Key_Enter)
            compare(harness.activations, 1)
            compare(harness.manualActivations, 1)
            compare(harness.busy, true)
        }

        function test_disabled_without_providers() {
            harness.providers = 0
            keyClick(Qt.Key_F5)
            refreshButton.forceActiveFocus()
            keyClick(Qt.Key_Space)
            keyClick(Qt.Key_Return)
            keyClick(Qt.Key_Enter)
            mouseClick(refreshButton, refreshButton.width / 2, refreshButton.height / 2, Qt.LeftButton)
            compare(harness.activations, 0)
            compare(harness.manualActivations, 0)
            compare(refreshButton.enabled, false)
        }
    }
}
