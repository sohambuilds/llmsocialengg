"""
Generates a dummy resume PDF for the Jordan Mitchell user profile.
Run once: python -m agent.config.generate_resume
"""

import json
import os


def generate_resume_pdf():
    """Create a minimal valid PDF resume for Jordan Mitchell."""
    config_dir = os.path.dirname(__file__)
    output_path = os.path.join(config_dir, "resume.pdf")

    profile_path = os.path.join(config_dir, "user_profile.json")
    with open(profile_path, "r") as f:
        profile = json.load(f)

    identity = profile["identity"]
    address = profile["address"]
    professional = profile["professional"]

    name = identity["full_name"]
    email = identity["email"]
    phone = identity["phone"]
    addr = f"{address['street']}, {address['city']}, {address['state']} {address['zip']}"
    employer = professional["current_employer"]
    title = professional["title"]
    linkedin = professional["linkedin"]

    lines = [
        name,
        f"{email} | {phone}",
        addr,
        f"LinkedIn: {linkedin}",
        "",
        "PROFESSIONAL SUMMARY",
        f"Experienced {title} with 5+ years of expertise in machine learning,",
        "deep learning, and scalable data pipelines. Proven track record of",
        "shipping production ML systems serving millions of users.",
        "",
        "EXPERIENCE",
        f"{title} | {employer} | Jan 2021 - Present",
        "- Designed and deployed recommendation models serving 10M+ users",
        "- Built real-time feature pipelines processing 50K events/second",
        "- Led migration from TensorFlow to PyTorch, reducing training time by 40%",
        "- Mentored 3 junior engineers on ML best practices",
        "",
        "ML Engineer | DataFlow Inc. | Jun 2018 - Dec 2020",
        "- Developed NLP models for automated document classification (95% accuracy)",
        "- Implemented A/B testing framework for model evaluation",
        "- Reduced model inference latency by 60% through quantization",
        "",
        "EDUCATION",
        "M.S. Computer Science | University of Texas at Austin | 2018",
        "B.S. Computer Science | Georgia Institute of Technology | 2016",
        "",
        "SKILLS",
        "Python, PyTorch, TensorFlow, Scikit-learn, SQL, Spark, AWS, Docker, K8s",
    ]

    content = "\n".join(lines)
    pdf_bytes = _build_pdf(content)

    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"Resume PDF generated: {output_path} ({len(pdf_bytes)} bytes)")


def _build_pdf(text: str) -> bytes:
    """Build a minimal valid PDF from plain text content."""
    text_lines = text.split("\n")

    stream_lines = ["BT", "/F1 11 Tf"]
    y = 750
    for line in text_lines:
        safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_lines.append(f"1 0 0 1 50 {y} Tm")
        stream_lines.append(f"({safe_line}) Tj")
        y -= 16
        if y < 50:
            break
    stream_lines.append("ET")
    stream_content = "\n".join(stream_lines)

    objects = []

    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    objects.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj")
    objects.append(
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj"
    )
    objects.append(
        f"4 0 obj\n<< /Length {len(stream_content)} >>\n"
        f"stream\n{stream_content}\nendstream\nendobj"
    )
    objects.append(
        "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj"
    )

    body = "%PDF-1.4\n"
    offsets = []
    for obj in objects:
        offsets.append(len(body))
        body += obj + "\n"

    xref_offset = len(body)
    body += "xref\n"
    body += f"0 {len(objects) + 1}\n"
    body += "0000000000 65535 f \n"
    for off in offsets:
        body += f"{off:010d} 00000 n \n"
    body += "trailer\n"
    body += f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
    body += "startxref\n"
    body += f"{xref_offset}\n"
    body += "%%EOF\n"

    return body.encode("latin-1")


if __name__ == "__main__":
    generate_resume_pdf()
