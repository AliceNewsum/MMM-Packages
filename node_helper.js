const NodeHelper = require("node_helper");
const { exec } = require("child_process");
const path = require("path");
const fs = require("fs");

module.exports = NodeHelper.create({
    start: function() {
        console.log("MMM-Packages helper started");
        this.config = null;
    },

    socketNotificationReceived: function(notification, payload) {
        if (notification === "SET_CONFIG") {
            this.config = payload;
            this.writeAccountsConfig();
        } else if (notification === "FETCH_PACKAGES") {
            this.fetchPackages();
        }
    },

    writeAccountsConfig: function() {
        if (!this.config) return;
        const configData = {
            accounts: this.config.accounts || [],
            lookbackDays: this.config.lookbackDays || 1,
            maxPackages: this.config.maxPackages || 5,
        };
        const configPath = path.join(__dirname, "accounts_config.json");
        fs.writeFileSync(configPath, JSON.stringify(configData, null, 2), "utf8");
    },

    fetchPackages: function() {
        const self = this;
        const scriptPath = path.join(__dirname, "fetch_packages.py");
        const configPath = path.join(__dirname, "accounts_config.json");
        exec("python3 " + JSON.stringify(scriptPath) + " " + JSON.stringify(configPath), (error, stdout, stderr) => {
            if (error) {
                console.error("MMM-Packages fetch error:", error.message);
            }
            if (stderr) {
                console.error("MMM-Packages stderr:", stderr);
            }
            const dataPath = path.join(__dirname, "packages_data.json");
            if (fs.existsSync(dataPath)) {
                try {
                    const data = JSON.parse(fs.readFileSync(dataPath, "utf8"));
                    self.sendSocketNotification("PACKAGES_DATA", data);
                } catch (e) {
                    console.error("MMM-Packages JSON parse error:", e.message);
                }
            }
        });
    }
});
