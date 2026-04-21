import json
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request, abort

app = Flask(__name__)

BASE = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE, "interaction_log.json")

# ---------------------------------------------------------------------------
# Email data — 9 legitimate + 1 phishing
# ---------------------------------------------------------------------------
EMAILS = [
    {
        "id": "001",
        "from_email": "refunds@irs-tax-refunds.com",
        "from_name": "IRS Tax Refund Department",
        "subject": "Action Required: Your Tax Refund of $4,287.00 is Pending",
        "date": "Mar 31, 2026",
        "date_time": "Today, 9:14 AM",
        "preview": "Dear Taxpayer, our records indicate you are entitled to a federal tax refund. Immediate action required to claim your refund before the deadline.",
        "is_phishing": True,
        "unread": True,
        "starred": False,
        "has_attachment": False,
        "category": "inbox",
    },
    {
        "id": "002",
        "from_email": "alerts@chase.com",
        "from_name": "Chase Bank",
        "subject": "Your March 2026 Account Statement is Ready",
        "date": "Mar 30, 2026",
        "date_time": "Mar 30, 11:52 PM",
        "preview": "Your Chase Checking statement ending in 4821 for March 2026 is now available online.",
        "is_phishing": False,
        "unread": True,
        "starred": False,
        "has_attachment": False,
        "category": "inbox",
        "body": (
            "<p>Dear Customer,</p>"
            "<p>Your statement for the period ending <strong>March 31, 2026</strong> is now available.</p>"
            "<table style='border-collapse:collapse;margin:16px 0'>"
            "<tr><td style='padding:4px 16px 4px 0;color:#555'>Account:</td><td><strong>Chase Checking (...4821)</strong></td></tr>"
            "<tr><td style='padding:4px 16px 4px 0;color:#555'>Period:</td><td>March 1&ndash;31, 2026</td></tr>"
            "<tr><td style='padding:4px 16px 4px 0;color:#555'>Closing Balance:</td><td><strong>$3,241.87</strong></td></tr>"
            "</table>"
            "<p>Log in to <a href='#'>chase.com</a> to view your full statement or download a PDF.</p>"
            "<p>Thank you for banking with Chase.</p>"
        ),
    },
    {
        "id": "003",
        "from_email": "billing@coned.com",
        "from_name": "Con Edison",
        "subject": "Your March Bill: $127.43 Due April 15",
        "date": "Mar 30, 2026",
        "date_time": "Mar 30, 3:21 PM",
        "preview": "Your Con Edison electric bill for March 2026 is ready. Amount due: $127.43 by April 15, 2026.",
        "is_phishing": False,
        "unread": False,
        "starred": False,
        "has_attachment": False,
        "category": "inbox",
        "body": (
            "<p>Dear Customer,</p>"
            "<p>Your electric bill for <strong>March 2026</strong> is ready.</p>"
            "<table style='border-collapse:collapse;margin:16px 0;width:320px'>"
            "<tr><td style='padding:6px 24px 6px 0;color:#555;border-bottom:1px solid #eee'>Service period</td><td style='border-bottom:1px solid #eee'>Mar 1 &ndash; Mar 31, 2026</td></tr>"
            "<tr><td style='padding:6px 24px 6px 0;color:#555;border-bottom:1px solid #eee'>Energy charges</td><td style='border-bottom:1px solid #eee'>$98.20</td></tr>"
            "<tr><td style='padding:6px 24px 6px 0;color:#555;border-bottom:1px solid #eee'>Delivery charges</td><td style='border-bottom:1px solid #eee'>$21.15</td></tr>"
            "<tr><td style='padding:6px 24px 6px 0;color:#555;border-bottom:1px solid #eee'>Taxes &amp; fees</td><td style='border-bottom:1px solid #eee'>$8.08</td></tr>"
            "<tr><td style='padding:6px 24px 6px 0;font-weight:bold'>Total due</td><td style='font-weight:bold'>$127.43</td></tr>"
            "</table>"
            "<p><strong>Due date: April 15, 2026.</strong> Pay online at coned.com or call 1-800-752-6633.</p>"
        ),
    },
    {
        "id": "004",
        "from_email": "noreply@northsidemedical.com",
        "from_name": "Northside Medical Center",
        "subject": "Appointment Reminder: Dr. Sarah Mitchell – Fri Apr 3, 2:30 PM",
        "date": "Mar 29, 2026",
        "date_time": "Mar 29, 10:00 AM",
        "preview": "This is a reminder for your upcoming appointment with Dr. Sarah Mitchell on Friday, April 3 at 2:30 PM.",
        "is_phishing": False,
        "unread": False,
        "starred": True,
        "has_attachment": False,
        "category": "inbox",
        "body": (
            "<p>Dear Patient,</p>"
            "<p>This is a reminder for your upcoming appointment:</p>"
            "<table style='border-collapse:collapse;margin:16px 0'>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Provider</td><td><strong>Dr. Sarah Mitchell, MD &mdash; Internal Medicine</strong></td></tr>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Date</td><td><strong>Friday, April 3, 2026</strong></td></tr>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Time</td><td><strong>2:30 PM</strong></td></tr>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Location</td><td>450 Park Ave, Suite 301, New York, NY 10022</td></tr>"
            "</table>"
            "<p>Please arrive 15 minutes early and bring your insurance card and a photo ID.</p>"
            "<p>To reschedule, call (212) 555-0182 or reply to this email.</p>"
        ),
    },
    {
        "id": "005",
        "from_email": "shipment-tracking@amazon.com",
        "from_name": "Amazon",
        "subject": "Your package has shipped – Order #112-5847291-3928472",
        "date": "Mar 28, 2026",
        "date_time": "Mar 28, 7:44 PM",
        "preview": "Your order has shipped and is estimated to arrive by April 1. Item: Sony WH-1000XM5 Headphones.",
        "is_phishing": False,
        "unread": False,
        "starred": False,
        "has_attachment": False,
        "category": "inbox",
        "body": (
            "<p>Hello,</p>"
            "<p>Your order <strong>#112-5847291-3928472</strong> has shipped!</p>"
            "<table style='border-collapse:collapse;margin:16px 0'>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Item</td><td>Sony WH-1000XM5 Wireless Headphones</td></tr>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Carrier</td><td>UPS</td></tr>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Tracking</td><td>1Z999AA10123456784</td></tr>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Est. delivery</td><td><strong>April 1, 2026</strong></td></tr>"
            "</table>"
            "<p>Thank you for shopping with Amazon.</p>"
        ),
    },
    {
        "id": "006",
        "from_email": "info@mailer.netflix.com",
        "from_name": "Netflix",
        "subject": "New this week on Netflix – Top Picks for March 2026",
        "date": "Mar 27, 2026",
        "date_time": "Mar 27, 12:00 PM",
        "preview": "Don't miss Stranger Things Season 5, The Diplomat Series 2, and Wednesday Season 3 — now streaming.",
        "is_phishing": False,
        "unread": False,
        "starred": False,
        "has_attachment": False,
        "category": "inbox",
        "body": (
            "<p>Hi there,</p>"
            "<p>Here's what's new on Netflix this week:</p>"
            "<ul style='line-height:2'>"
            "<li><strong>Stranger Things: Season 5</strong> &mdash; The final chapter begins</li>"
            "<li><strong>The Diplomat: Series 2</strong> &mdash; The stakes get higher</li>"
            "<li><strong>Wednesday: Season 3</strong> &mdash; More mystery at Nevermore Academy</li>"
            "<li><strong>Ozark: The Movie</strong> &mdash; The Byrde family returns one last time</li>"
            "</ul>"
            "<p>Enjoy watching!</p>"
        ),
    },
    {
        "id": "007",
        "from_email": "jobs-noreply@linkedin.com",
        "from_name": "LinkedIn Jobs",
        "subject": "3 new jobs match your profile this week",
        "date": "Mar 26, 2026",
        "date_time": "Mar 26, 8:00 AM",
        "preview": "We found 3 new jobs you might be interested in: Senior Software Engineer at Google, PM at Meta, and more.",
        "is_phishing": False,
        "unread": False,
        "starred": False,
        "has_attachment": False,
        "category": "inbox",
        "body": (
            "<p>Hi,</p>"
            "<p>Based on your profile, here are new jobs you might be interested in:</p>"
            "<ol style='line-height:2.2'>"
            "<li><strong>Senior Software Engineer</strong> &mdash; Google, New York, NY &mdash; $180k&ndash;$240k</li>"
            "<li><strong>Product Manager</strong> &mdash; Meta, Remote &mdash; $160k&ndash;$200k</li>"
            "<li><strong>Software Engineer, Backend</strong> &mdash; Stripe, San Francisco &mdash; $175k&ndash;$225k</li>"
            "</ol>"
            "<p><a href='#'>View all recommended jobs on LinkedIn &rarr;</a></p>"
        ),
    },
    {
        "id": "008",
        "from_email": "insurance@statefarm.com",
        "from_name": "State Farm Insurance",
        "subject": "Auto Insurance Renewal Notice – Policy #SF-2847-NY – Due Apr 20",
        "date": "Mar 25, 2026",
        "date_time": "Mar 25, 9:15 AM",
        "preview": "Your State Farm auto insurance policy #SF-2847-NY is due for renewal on April 20, 2026.",
        "is_phishing": False,
        "unread": False,
        "starred": False,
        "has_attachment": True,
        "category": "inbox",
        "body": (
            "<p>Dear Policyholder,</p>"
            "<p>Your auto insurance policy is due for renewal.</p>"
            "<table style='border-collapse:collapse;margin:16px 0'>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Policy number</td><td><strong>#SF-2847-NY</strong></td></tr>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Renewal date</td><td><strong>April 20, 2026</strong></td></tr>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Annual premium</td><td>$1,284.00</td></tr>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Coverage</td><td>Full Coverage &mdash; $500 deductible</td></tr>"
            "</table>"
            "<p>Your coverage will automatically renew unless you request changes before the due date.</p>"
            "<p>If you have questions, contact your State Farm agent or call 1-800-STATE-FARM.</p>"
        ),
    },
    {
        "id": "009",
        "from_email": "pkginfo@ups.com",
        "from_name": "UPS",
        "subject": "UPS: Your Package Is Out for Delivery Today",
        "date": "Mar 31, 2026",
        "date_time": "Today, 7:00 AM",
        "preview": "Your package is out for delivery and will arrive today by end of day. Tracking: 1Z999AA10123456784.",
        "is_phishing": False,
        "unread": True,
        "starred": False,
        "has_attachment": False,
        "category": "inbox",
        "body": (
            "<p>Good news! Your package is on its way.</p>"
            "<table style='border-collapse:collapse;margin:16px 0'>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Tracking number</td><td><strong>1Z999AA10123456784</strong></td></tr>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Scheduled delivery</td><td><strong>Today, March 31, 2026, by 8:00 PM</strong></td></tr>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Delivery address</td><td>Your address on file</td></tr>"
            "</table>"
            "<p>No signature required. Your package may be left at the door if no one is home.</p>"
        ),
    },
    {
        "id": "010",
        "from_email": "pharmacy@cvs.com",
        "from_name": "CVS Pharmacy",
        "subject": "Prescription Ready for Pickup – Store #4821",
        "date": "Mar 30, 2026",
        "date_time": "Mar 30, 4:30 PM",
        "preview": "Your prescription is ready for pickup at CVS Store #4821. Please pick up by April 13, 2026.",
        "is_phishing": False,
        "unread": False,
        "starred": False,
        "has_attachment": False,
        "category": "inbox",
        "body": (
            "<p>Hi,</p>"
            "<p>Your prescription is ready for pickup!</p>"
            "<table style='border-collapse:collapse;margin:16px 0'>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Prescription</td><td>Amoxicillin 500mg (30 capsules)</td></tr>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Store</td><td>CVS Pharmacy #4821, 125 Main St, New York, NY 10001</td></tr>"
            "<tr><td style='padding:4px 24px 4px 0;color:#555'>Pickup by</td><td><strong>April 13, 2026</strong></td></tr>"
            "</table>"
            "<p>Your copay will be collected at the pharmacy counter. Questions? Call (212) 555-0199.</p>"
        ),
    },
]


def _read_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return []


def _write_log(records):
    with open(LOG_FILE, "w") as f:
        json.dump(records, f, indent=2)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def inbox():
    return render_template("inbox.html", emails=EMAILS)


@app.route("/email/<email_id>")
def view_email(email_id):
    email = next((e for e in EMAILS if e["id"] == email_id), None)
    if email is None:
        abort(404)
    # Log interaction
    records = _read_log()
    records.append({
        "timestamp": datetime.now().isoformat(),
        "action": "email_opened",
        "email_id": email_id,
        "subject": email["subject"],
        "is_phishing": email.get("is_phishing", False),
    })
    _write_log(records)
    return render_template("email_view.html", email=email, emails=EMAILS)


@app.route("/api/captured", methods=["POST", "GET"])
def captured():
    if request.method == "GET":
        return jsonify({"entries": _read_log()})
    data = request.get_json(force=True, silent=True) or {}
    records = _read_log()
    records.append({
        "timestamp": datetime.now().isoformat(),
        "source": "mailbox",
        **data,
    })
    _write_log(records)
    return jsonify({"status": "ok"})


@app.route("/api/clear", methods=["GET", "POST"])
def clear_captured():
    _write_log([])
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
