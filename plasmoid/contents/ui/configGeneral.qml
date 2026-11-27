import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.plasma5support as P5Support
import QtCore

ColumnLayout {
    id: page
    spacing: Kirigami.Units.smallSpacing

    property string stepfunStatus: "…"
    property string stepfunDetail: ""
    property bool stepfunBusy: false

    property string mimoStatus: "…"
    property string mimoDetail: ""
    property bool mimoBusy: false
    property bool cfg_enableMimo: false
    property string cfg_mimoRegion: "sgp"

    function filesystemPath(urlOrPath) {
        var s = String(urlOrPath)
        if (s.indexOf("file://") === 0)
            return decodeURIComponent(s.substring(7))
        return s
    }

    function shellQuote(path) {
        return "'" + String(path).replace(/'/g, "'\\''") + "'"
    }

    function dataPath() {
        return filesystemPath(StandardPaths.writableLocation(StandardPaths.GenericDataLocation))
    }

    function helperCmd(action) {
        var lib = dataPath() + "/horizon/collector/stepfun_auth_helper.py"
        return "python3 " + shellQuote(lib) + " " + action
    }

    function applyHelperResult(stdout, exitCode) {
        var line = String(stdout || "").trim().split("\n").pop()
        if (line === "working") {
            stepfunStatus = "Configured · working"
            stepfunDetail = "Token accepted by StepFun."
        } else if (line === "auth_failed") {
            stepfunStatus = "Configured · needs authentication"
            stepfunDetail = "A token is stored, but StepFun rejected it after a single automatic refresh attempt. Copy a fresh Oasis-Token from platform.stepfun.ai and save again."
        } else if (line === "unavailable") {
            stepfunStatus = "Configured · unavailable"
            stepfunDetail = "StepFun could not be reached or verified right now. Your stored token was kept; try Check status again when online."
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
        } else {
            stepfunStatus = "Helper error"
            stepfunDetail = "Helper failed to run — reinstall with scripts/install.sh."
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

    function normalizedMimoRegion() {
        var r = String(mimoRegionBox.currentText || "sgp").trim()
        return (r === "sgp" || r === "cn" || r === "ams") ? r : "sgp"
    }

    function mimoHelperCmd(action) {
        var lib = dataPath() + "/horizon/collector/mimo_auth_helper.py"
        return "python3 " + shellQuote(lib) + " " + action + " " + normalizedMimoRegion()
    }

    function applyMimoHelperResult(stdout, exitCode) {
        var line = String(stdout || "").trim().split("\n").pop()
        if (line === "working") {
            mimoStatus = "Configured · working"
            mimoDetail = "Key accepted by Xiaomi MiMo (" + normalizedMimoRegion() + ")."
        } else if (line === "auth_failed") {
            mimoStatus = "Configured · needs authentication"
            mimoDetail = "Xiaomi MiMo rejected the key for region " + normalizedMimoRegion() + ". Check the tp- key and region, then save again."
        } else if (line === "unavailable") {
            mimoStatus = "Configured · unavailable"
            mimoDetail = "Xiaomi MiMo could not be reached right now. Your stored key was kept; try Check status again when online."
        } else if (line === "missing" || line === "cleared") {
            mimoStatus = "Not configured"
            mimoDetail = ""
        } else if (line === "empty") {
            mimoStatus = "Not saved"
            mimoDetail = "Clipboard was empty. Copy your tp- key from the Xiaomi MiMo Token Plan console, then click Save key."
        } else if (line === "invalid") {
            mimoStatus = "Not saved"
            mimoDetail = "Clipboard did not look like a Xiaomi MiMo tp- key (8-256 characters, no whitespace)."
        } else if (line === "store_error") {
            mimoStatus = "Store error"
            mimoDetail = "Could not access KWallet."
        } else {
            mimoStatus = "Helper error"
            mimoDetail = "Helper failed to run — reinstall with scripts/install.sh."
        }
    }

    function refreshMimoStatus() {
        mimoBusy = true
        mimoDetail = ""
        mimoExec.exec(mimoHelperCmd("status"))
    }

    function saveMimoKeyFromClipboard() {
        mimoBusy = true
        mimoDetail = "Saving…"
        mimoKeyField.text = ""
        mimoExec.exec(mimoHelperCmd("clipboard"))
    }

    function clearMimoKey() {
        mimoBusy = true
        mimoDetail = ""
        mimoExec.exec(mimoHelperCmd("clear"))
    }

    Component.onCompleted: {
        refreshStepfunStatus()
        refreshMimoStatus()
    }

    P5Support.DataSource {
        id: authExec
        engine: "executable"
        connectedSources: []
        onNewData: function (sourceName, data) {
            var stdout = data["stdout"] ? String(data["stdout"]).trim() : ""
            var exitCode = (data && data["exit code"] !== undefined) ? Number(data["exit code"]) : 0
            disconnectSource(sourceName)
            page.stepfunBusy = false
            page.applyHelperResult(stdout, exitCode)
        }
        function exec(cmd) {
            connectSource(cmd)
        }
    }

    P5Support.DataSource {
        id: mimoExec
        engine: "executable"
        connectedSources: []
        onNewData: function (sourceName, data) {
            var stdout = data["stdout"] ? String(data["stdout"]).trim() : ""
            var exitCode = (data && data["exit code"] !== undefined) ? Number(data["exit code"]) : 0
            disconnectSource(sourceName)
            page.mimoBusy = false
            page.applyMimoHelperResult(stdout, exitCode)
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
        PlasmaComponents.CheckBox {
            text: i18n("Claude")
            checked: plasmoid.configuration.enableClaude
            onCheckedChanged: plasmoid.configuration.enableClaude = checked
        }
        PlasmaComponents.CheckBox {
            id: mimoCheck
            text: "Xiaomi MiMo"
            checked: page.cfg_enableMimo
            onCheckedChanged: page.cfg_enableMimo = checked
        }

        QQC2.ComboBox {
            id: mimoRegionBox
            Kirigami.FormData.label: "MiMo region"
            model: ["sgp", "cn", "ams"]
            currentIndex: {
                var idx = model.indexOf(String(page.cfg_mimoRegion || "sgp"))
                return idx >= 0 ? idx : 0
            }
            onActivated: page.cfg_mimoRegion = model[currentIndex]
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

    Kirigami.Separator {
        Layout.fillWidth: true
        Layout.topMargin: Kirigami.Units.smallSpacing
        Layout.bottomMargin: Kirigami.Units.smallSpacing
    }

    PlasmaComponents.Label {
        Layout.fillWidth: true
        text: "Xiaomi MiMo credential"
        font.bold: true
    }
    PlasmaComponents.Label {
        Layout.fillWidth: true
        text: "Status: " + page.mimoStatus
        wrapMode: Text.WordWrap
        opacity: 0.9
    }
    PlasmaComponents.Label {
        Layout.fillWidth: true
        visible: page.mimoDetail.length > 0
        wrapMode: Text.WordWrap
        text: page.mimoDetail
        opacity: 0.75
    }
    PlasmaComponents.Label {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: "1. Copy your tp- key from the Xiaomi MiMo Token Plan console. 2. Optional: paste here to confirm you copied it. 3. Click Save key (reads the clipboard; stored only in KWallet, never in Plasma config). MiMo refreshes only on manual Refresh."
        opacity: 0.7
    }

    QQC2.TextField {
        id: mimoKeyField
        Layout.fillWidth: true
        echoMode: TextInput.Password
        placeholderText: "MiMo tp- key (optional paste check)"
        enabled: !page.mimoBusy
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing
        PlasmaComponents.Button {
            text: "Save key"
            enabled: !page.mimoBusy
            onClicked: page.saveMimoKeyFromClipboard()
        }
        PlasmaComponents.Button {
            text: "Clear"
            enabled: !page.mimoBusy && page.mimoStatus.indexOf("Configured") === 0
            onClicked: page.clearMimoKey()
        }
        PlasmaComponents.Button {
            text: "Check status"
            enabled: !page.mimoBusy
            onClicked: page.refreshMimoStatus()
        }
    }
}
