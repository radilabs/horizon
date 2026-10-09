import QtQuick
import QtQuick.Controls as QQC2
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

    QQC2.ToolButton {
        id: refreshButton
        text: "Refresh"
        focus: true
        enabled: providers > 0
        Accessible.name: busy ? "Refreshing" : "Refresh"
        onClicked: refresh()
        Keys.onReturnPressed: if (enabled) refresh()
        Keys.onEnterPressed: if (enabled) refresh()
        Keys.onSpacePressed: if (enabled) refresh()
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
    }

    function test_f5_refreshes() {
        keyClick(Qt.Key_F5)
        compare(activations, 1)
        compare(busy, true)
        compare(refreshButton.Accessible.name, "Refreshing")
    }

    function test_disabled_without_providers() {
        providers = 0
        keyClick(Qt.Key_F5)
        refreshButton.forceActiveFocus()
        keyClick(Qt.Key_Return)
        compare(activations, 0)
        compare(refreshButton.enabled, false)
    }
}
