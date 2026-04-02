# MMM-Packages

A [MagicMirror²](https://magicmirror.builders/) module that scans your IMAP email accounts for shipping and delivery notifications and displays package tracking status on your mirror.

Unlike other package tracking modules, MMM-Packages works by reading the shipping notification emails you already receive from carriers like Amazon, UPS, FedEx, and USPS. No API keys or tracking number entry required -- just point it at your email accounts and it finds your packages automatically.

![Screenshot](screenshot.png)

## Features

- Scans multiple IMAP email accounts for shipping notifications
- Detects packages from Amazon, UPS, FedEx, and USPS
- Shows delivery status: Shipped, Out for Delivery, or Delivered
- Extracts item names from email subjects when available
- Cycles between carrier/status and item name display
- Uses `BODY.PEEK[]` to fetch emails without marking them as read
- Deduplicates packages across multiple notification emails
- Fully configurable through MagicMirror's `config.js`

## Installation

1. Navigate to your MagicMirror modules directory:

```bash
cd ~/MagicMirror/modules
```

2. Clone this repository:

```bash
git clone https://github.com/MatthewNewsum/MMM-Packages.git
```

3. Install the Python dependency:

```bash
pip3 install python-dotenv
```

Note: The module requires Python 3 with the `imaplib`, `email`, `json`, `re`, and `datetime` standard library modules (all included with Python).

## Configuration

Add the following to the `modules` array in your MagicMirror `config/config.js` file:

```javascript
{
    module: "MMM-Packages",
    position: "bottom_left",
    config: {
        accounts: [
            {
                server: "imap.gmail.com",
                username: "you@gmail.com",
                password: "your-app-password",
            },
            {
                server: "imap.mail.yahoo.com",
                username: "you@yahoo.com",
                password: "your-app-password",
            },
        ],
        updateInterval: 5 * 60 * 1000,
        cycleInterval: 4000,
        lookbackDays: 1,
        maxPackages: 5,
    }
},
```

### Gmail Setup

For Gmail accounts, you must use an App Password rather than your regular password:

1. Enable 2-Step Verification on your Google account.
2. Go to [App Passwords](https://myaccount.google.com/apppasswords).
3. Generate a new app password for "Mail".
4. Use that generated password in the config above.

### Yahoo Setup

For Yahoo accounts, generate an app password at [Yahoo Account Security](https://login.yahoo.com/account/security).

## Config Options

| Option           | Description                                          | Default           |
| ---------------- | ---------------------------------------------------- | ----------------- |
| `accounts`       | Array of IMAP account objects (see above)            | `[]`              |
| `updateInterval` | How often to check email for updates (milliseconds)  | `300000` (5 min)  |
| `cycleInterval`  | How often to cycle between status and item name (ms) | `4000` (4 sec)    |
| `lookbackDays`   | How many days back to search for shipping emails     | `1`               |
| `maxPackages`    | Maximum number of packages to display                | `5`               |

Each account object in the `accounts` array requires:

| Field      | Description                        | Example                  |
| ---------- | ---------------------------------- | ------------------------ |
| `server`   | IMAP server hostname               | `"imap.gmail.com"`      |
| `username` | Email address / login              | `"you@gmail.com"`       |
| `password` | Password or app-specific password  | `"abcd efgh ijkl mnop"` |

## How It Works

1. On startup and at each `updateInterval`, the node helper writes your account configuration to a temporary JSON file and invokes the Python script.
2. The Python script connects to each configured IMAP account over SSL and searches the inbox for emails received within the `lookbackDays` window.
3. It checks each email's sender address against a list of known carrier addresses (Amazon, UPS, FedEx, USPS).
4. For matching emails, it determines the package status by scanning the subject and body for keywords like "has shipped", "out for delivery", or "delivered".
5. When possible, it extracts the item name from the email subject (e.g., quoted product names in Amazon confirmation emails).
6. Packages are deduplicated by carrier and item name, with status upgrades applied (e.g., if a "shipped" and "out for delivery" email exist for the same package, the more recent status wins).
7. Results are written to a JSON file that the node helper reads and sends to the front-end module for display.
8. The front-end cycles between showing carrier/status and item name for packages that have an identified item.

Emails are fetched using `BODY.PEEK[]` which does **not** mark messages as read, so your inbox is unaffected.

## Supported Carriers

- **Amazon** -- auto-confirm, shipment-tracking, ship-confirm, delivery-tracking, order-update
- **UPS** -- tracking, pkginfo, noreply
- **FedEx** -- fedex, trk, noreply
- **USPS** -- usps, auto-reply, noreply

## License

MIT License. See [LICENSE](LICENSE) for details.
