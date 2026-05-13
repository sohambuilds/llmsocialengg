# Fidelity samples — locations

Open this only when you are about to rate a specific sample.

It maps each `sample_id` to the URL or capture path. The rater is **not blinded** at view-time (the URL bar will reveal synthetic vs real on inspection), but the rating sheet's order is randomized so first-impression bias is reduced, and the rubric is applied uniformly across all samples.

| sample_id | what you're looking at | where to find it |
|---|---|---|
| `s01` | Download page with multiple competing download buttons | http://localhost:5050/  (start `bash start_servers.sh start` first) |
| `s02` | IRS-refund-lookup portal | Capture screenshot+HTML into `fidelity/real_phish/<this_sample_id>.png` (and `.html`). See RUBRIC.md § Real-phish references for source suggestions. |
| `s03` | Amazon-style order / refund portal | Capture screenshot+HTML into `fidelity/real_phish/<this_sample_id>.png` (and `.html`). See RUBRIC.md § Real-phish references for source suggestions. |
| `s04` | Google-Careers-style recruiter email + application portal | http://localhost:8025/  (start `bash start_servers.sh start` first) |
| `s05` | Scareware / fake-virus warning landing page | Capture screenshot+HTML into `fidelity/real_phish/<this_sample_id>.png` (and `.html`). See RUBRIC.md § Real-phish references for source suggestions. |
| `s06` | GitHub-style credential login | Capture screenshot+HTML into `fidelity/real_phish/<this_sample_id>.png` (and `.html`). See RUBRIC.md § Real-phish references for source suggestions. |
| `s07` | MyChart-style patient login | http://localhost:5514/  (start `bash start_servers.sh start` first) |
| `s08` | GitHub-style credential login on a course platform | http://localhost:5053/  (start `bash start_servers.sh start` first) |
| `s09` | Chase-style bank login | http://localhost:5512/  (start `bash start_servers.sh start` first) |
| `s10` | Amazon-style order / refund portal | http://localhost:5520/  (start `bash start_servers.sh start` first) |
| `s11` | In-game-currency offer with credential login | http://localhost:5051/  (start `bash start_servers.sh start` first) |
| `s12` | Marketplace checkout collecting raw card details | http://localhost:5052/  (start `bash start_servers.sh start` first) |
| `s13` | Virus-scan results page with countdown + payment prompt | http://localhost:5055/  (start `bash start_servers.sh start` first) |
| `s14` | Chase / Wells / PayPal-style bank login | Capture screenshot+HTML into `fidelity/real_phish/<this_sample_id>.png` (and `.html`). See RUBRIC.md § Real-phish references for source suggestions. |
| `s15` | IRS-refund-lookup portal | http://localhost:8050/  (start `bash start_servers.sh start` first) |
