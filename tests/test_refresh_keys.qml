import QtQuick
import org.kde.plasma.components as PlasmaComponents
import QtTest

TestCase {
    name: "RefreshKeys"
    when: windowShown
    width: 240
    height: 80

    property int activations: 0
    property int providers: 2
    property bool busy: false

    function refresh() {
        if (providers <= 0)
            return
        busy = true
        activations += 1
    }

    PlasmaComponents.ToolButton {
        id: refreshButton
        text: "Refresh"
        focus: true
        enabled: providers > 0
        Accessible.name: busy ? "Refreshing" : "Refresh"
        onClicked: refresh()
        Keys.onReturnPressed: function (event) {
            if (enabled) {
                event.accepted = true
                refresh()
            }
        }
        Keys.onEnterPressed: function (event) {
            if (enabled) {
                event.accepted = true
                refresh()
            }
        }
    }

    Shortcut {
        sequences: ["F5"]
        context: Qt.WindowShortcut
        enabled: providers > 0
        onActivated: refresh()
    }

    function init() {
        activations = 0
        busy = false
        providers = 2
        refreshButton.forceActiveFocus()
    }

    function test_f5_refreshes() {
        keyClick(Qt.Key_F5)
        compare(activations, 1)
        compare(busy, true)
        compare(refreshButton.Accessible.name, "Refreshing")
    }

    function test_space_activates_once() {
        keyClick(Qt.Key_Space)
        compare(activations, 1)
        compare(busy, true)
    }

    function test_return_activates_once() {
        keyClick(Qt.Key_Return)
        compare(activations, 1)
        compare(busy, true)
    }

    function test_enter_activates_once() {
        keyClick(Qt.Key_Enter)
        compare(activations, 1)
        compare(busy, true)
    }

    function test_disabled_without_providers() {
        providers = 0
        keyClick(Qt.Key_F5)
        refreshButton.forceActiveFocus()
        keyClick(Qt.Key_Space)
        keyClick(Qt.Key_Return)
        keyClick(Qt.Key_Enter)
        compare(activations, 0)
        compare(refreshButton.enabled, false)
    }
}
