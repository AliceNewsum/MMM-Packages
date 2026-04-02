Module.register("MMM-Packages", {
    defaults: {
        accounts: [],
        updateInterval: 5 * 60 * 1000,
        cycleInterval: 4000,
        lookbackDays: 1,
        maxPackages: 5,
    },

    start: function() {
        this.packages = [];
        this.cycleIndex = {};
        this.sendSocketNotification("SET_CONFIG", this.config);
        this.sendSocketNotification("FETCH_PACKAGES");
        setInterval(() => {
            this.sendSocketNotification("FETCH_PACKAGES");
        }, this.config.updateInterval);

        setInterval(() => {
            this.toggleCycle();
        }, this.config.cycleInterval);
    },

    toggleCycle: function() {
        if (!this.packages || this.packages.length === 0) return;
        this.packages.forEach((pkg, i) => {
            if (pkg.item) {
                this.cycleIndex[i] = !this.cycleIndex[i];
            }
        });
        this.updateDom(500);
    },

    socketNotificationReceived: function(notification, payload) {
        if (notification === "PACKAGES_DATA") {
            this.packages = payload;
            this.cycleIndex = {};
            this.updateDom();
        }
    },

    getDom: function() {
        const wrapper = document.createElement("div");
        wrapper.className = "mmm-packages";

        if (!this.packages || this.packages.length === 0) {
            wrapper.innerHTML = "<span class=\"pkg-none\">No deliveries expected</span>";
            return wrapper;
        }

        this.packages.forEach((pkg, i) => {
            const row = document.createElement("div");
            row.className = "pkg-row";

            const icon = document.createElement("span");
            icon.className = "pkg-icon";
            icon.innerHTML = "&#x1F4E6;";

            const info = document.createElement("span");
            info.className = "pkg-info";

            const showItem = pkg.item && this.cycleIndex[i];

            if (showItem) {
                info.innerHTML = "<span class=\"pkg-item\">" + pkg.item + "</span>";
            } else {
                const statusClass = pkg.status === "Delivered"
                    ? "pkg-status delivered"
                    : pkg.status === "Out for Delivery"
                        ? "pkg-status otd"
                        : "pkg-status";

                info.innerHTML = "<span class=\"pkg-carrier\">" + pkg.carrier + "</span>"
                    + " &mdash; "
                    + "<span class=\"" + statusClass + "\">" + pkg.status + "</span>";
            }

            row.appendChild(icon);
            row.appendChild(info);
            wrapper.appendChild(row);
        });

        return wrapper;
    },

    getStyles: function() {
        return ["MMM-Packages.css"];
    }
});
