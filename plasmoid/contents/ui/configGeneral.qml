import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as P5Support
import QtCore

ColumnLayout {
    id: page
    spacing: Kirigami.Units.smallSpacing

    property string stepfunStatus: "…"
    property string stepfunDetail: ""
    property bool stepfunBusy: false

    function filesystemPath(urlOrPath) {
        var s = String(urlOrPath)
        if (s.indexOf("file://") === 0)
            return decodeURIComponent(s.substring(7))
        return s
    }

    function homePath() {
        return filesystemPath(StandardPaths.writableLocation(StandardPaths.HomeLocation))
    }

    function helperCmd(action) {
        // Installed copy preferred; fall back to repo layout during dev.
        var lib = homePath() + "/.local/share/horizon/collector/stepfun_auth_helper.py"
        return "python3 \"" + lib + "\" " + action
    }

    function applyHelperResult(stdout) {
        var line = String(stdout || "").trim().split("\n").pop()
        if (line === "working") {
            stepfunStatus = "Configured · working"
            stepfunDetail = "Token accepted by StepFun."
        } else if (line === "auth_failed") {
            stepfunStatus = "Configured · needs authentication"
            stepfunDetail = "A token is stored, but StepFun rejected it. Copy a fresh Oasis-Token from platform.stepfun.ai and save again."
        } else if (line === "missing") {
            stepfunStatus = "Not configured"
            stepfunDetail = ""
        } else if (line === "empty") {
            stepfunStatus = "Not saved"
            stepfunDetail = "Clipboard was empty. Copy the Oasis-Token cookie from platform.stepfun.ai, then click Save token."
        } else if (line === "invalid") {
            stepfunStatus = "Not saved"
            stepfunDetail = "Clipboard did not look like an Oasis token. Copy the full Oasis-Token cookie value from platform.stepfun.ai."
        } else if (line === "store_error") {
            stepfunStatus = "Store error"
            stepfunDetail = "Could not access KWallet."
        } else if (line.length) {
            stepfunDetail = line
        }
    }

    function refreshStepfunStatus() {
        stepfunBusy = true
        stepfunDetail = ""
        authExec.exec(helperCmd("status"))
    }

    function saveTokenFromClipboard() {
        // Plasma's executable engine cannot pipe stdin without putting the
        // secret in argv. Save reads the system clipboard (copy from Zen,
        // then Save). The field is password-echo only for a visual check.
        stepfunBusy = true
        stepfunDetail = "Saving…"
        tokenField.text = ""
        authExec.exec(helperCmd("clipboard"))
    }

    function clearStepfunToken() {
        stepfunBusy = true
        stepfunDetail = ""
        authExec.exec(helperCmd("clear"))
    }

    Component.onCompleted: refreshStepfunStatus()

    P5Support.DataSource {
        id: authExec
        engine: "executable"
        connectedSources: []
        onNewData: function (sourceName, data) {
            var stdout = data["stdout"] ? String(data["stdout"]).trim() : ""
            disconnectSource(sourceName)
            stepfunBusy = false
            page.applyHelperResult(stdout)
        }
        function exec(cmd) {
            connectSource(cmd)
        }
    }

    Kirigami.FormLayout {
        Layout.fillWidth: true

        PlasmaComponents.CheckBox {
            Kirigami.FormData.label: i18n("Providers")
            text: i18n("Codex")
            checked: plasmoid.configuration.enableCodex
            onCheckedChanged: plasmoid.configuration.enableCodex = checked
        }
        PlasmaComponents.CheckBox {
            text: i18n("Cursor")
            checked: plasmoid.configuration.enableCursor
            onCheckedChanged: plasmoid.configuration.enableCursor = checked
        }
        PlasmaComponents.CheckBox {
            text: i18n("StepFun")
            checked: plasmoid.configuration.enableStepfun
            onCheckedChanged: plasmoid.configuration.enableStepfun = checked
        }

        QQC2.ComboBox {
            id: intervalBox
            Kirigami.FormData.label: i18n("Refresh interval")
            model: ["5", "10", "15", "30", "60"]
            currentIndex: {
                var v = String(plasmoid.configuration.refreshIntervalMinutes)
                var idx = model.indexOf(v)
                return idx >= 0 ? idx : model.indexOf("15")
            }
            displayText: currentText + " " + i18n("minutes")
            onActivated: plasmoid.configuration.refreshIntervalMinutes = parseInt(model[currentIndex], 10)
        }
    }

    Kirigami.Separator {
        Layout.fillWidth: true
        Layout.topMargin: Kirigami.Units.smallSpacing
        Layout.bottomMargin: Kirigami.Units.smallSpacing
    }

    PlasmaComponents.Label {
        Layout.fillWidth: true
        text: i18n("StepFun credential")
        font.bold: true
    }
    PlasmaComponents.Label {
        Layout.fillWidth: true
        text: i18n("Status: %1", page.stepfunStatus)
        wrapMode: Text.WordWrap
        opacity: 0.9
    }
    PlasmaComponents.Label {
        Layout.fillWidth: true
        visible: page.stepfunDetail.length > 0
        wrapMode: Text.WordWrap
        text: page.stepfunDetail
        opacity: 0.75
    }
    PlasmaComponents.Label {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: i18n("1. Copy the Oasis-Token cookie from platform.stepfun.ai. 2. Optional: paste here to confirm you copied it. 3. Click Save token (reads the clipboard; never stored in Plasma config).")
        opacity: 0.7
    }

    QQC2.TextField {
        id: tokenField
        Layout.fillWidth: true
        echoMode: TextInput.Password
        placeholderText: i18n("Oasis token (optional paste check)")
        enabled: !page.stepfunBusy
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing
        PlasmaComponents.Button {
            text: i18n("Save token")
            enabled: !page.stepfunBusy
            onClicked: page.saveTokenFromClipboard()
        }
        PlasmaComponents.Button {
            text: i18n("Remove token")
            enabled: !page.stepfunBusy && page.stepfunStatus.indexOf("Configured") === 0
            onClicked: page.clearStepfunToken()
        }
        PlasmaComponents.Button {
            text: i18n("Check status")
            enabled: !page.stepfunBusy
            onClicked: page.refreshStepfunStatus()
        }
    }
}
