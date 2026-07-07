"""
Generate 2-page resume PDFs for Alex and Marcelli, plus 3 new Alex resumes.
Uses fpdf2 for PDF generation with a clean, professional layout.
"""
from fpdf import FPDF
from pathlib import Path


class ResumePDF(FPDF):
    """Clean resume PDF with consistent formatting."""

    BLUE = (44, 62, 80)
    TEAL = (0, 150, 136)
    BLACK = (30, 30, 30)
    GRAY = (100, 100, 100)
    LIGHT_GRAY = (180, 180, 180)

    def __init__(self, accent_color=None):
        super().__init__()
        self.accent = accent_color or self.BLUE
        self.set_auto_page_break(auto=True, margin=20)

    def header_block(self, name, contact_line):
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(*self.BLACK)
        self.cell(0, 12, name, align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.GRAY)
        self.cell(0, 5, contact_line, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_draw_color(*self.accent)
        self.set_line_width(0.8)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def section_heading(self, title):
        self.ln(2)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*self.accent)
        self.cell(0, 7, title.upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self.LIGHT_GRAY)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def job_header(self, company, dates, title_line):
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(*self.BLACK)
        w = self.w - self.l_margin - self.r_margin
        self.cell(w * 0.65, 5.5, company, new_x="RIGHT")
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*self.GRAY)
        self.cell(w * 0.35, 5.5, dates, align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "I", 9.5)
        self.set_text_color(*self.GRAY)
        self.cell(0, 5, title_line, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def context_paragraph(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.BLACK)
        self.multi_cell(0, 4.5, text)
        self.ln(1)

    def bullet(self, text, bold_prefix=""):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.BLACK)
        self.cell(5, 4.5, "-")
        if bold_prefix:
            self.set_font("Helvetica", "B", 9)
            self.cell(self.get_string_width(bold_prefix) + 1, 4.5, bold_prefix)
            self.set_font("Helvetica", "", 9)
            self.multi_cell(0, 4.5, text)
        else:
            self.multi_cell(0, 4.5, text)
        self.ln(0.5)

    def summary_text(self, text):
        self.set_font("Helvetica", "I", 9.5)
        self.set_text_color(*self.BLACK)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def skills_line(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.BLACK)
        self.multi_cell(0, 4.5, text)
        self.ln(1)

    def edu_entry(self, school, detail, date=""):
        self.set_font("Helvetica", "B", 9.5)
        self.set_text_color(*self.BLACK)
        w = self.w - self.l_margin - self.r_margin
        self.cell(w * 0.7, 5, school, new_x="RIGHT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.GRAY)
        self.cell(w * 0.3, 5, date, align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "I", 9)
        self.cell(0, 4.5, detail, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)


# ===================================================================
# ALEX - AI Engineer 2-page
# ===================================================================

def generate_alex_ai_2page():
    pdf = ResumePDF()
    pdf.add_page()
    pdf.header_block("Alexander Moody",
        "(603) 943-0051  |  alexmoody1421@gmail.com  |  opentechnologyblog.com  |  opentechnologyapp.com")

    pdf.section_heading("Professional Summary")
    pdf.summary_text(
        "AI/automation engineer building production tools and applied AI content. "
        "Healthcare IT background with 4 years operating as primary automation engineer "
        "through high organizational change. Ships systems end-to-end - from requirements "
        "gathering through deployment and post-launch operations.")

    pdf.section_heading("Experience")

    pdf.job_header("Eleanor Health", "July 2022 - Present",
        "Senior IT Support Associate - Automation & Systems Engineering")
    pdf.context_paragraph(
        "Operated as the primary automation engineer for a 200-person fully remote behavioral health "
        "startup through significant organizational change - 8 direct managers in 4 years due to rapid "
        "growth and restructuring. Self-directed priorities, maintained system uptime, and delivered "
        "projects continuously regardless of leadership transitions.")
    pdf.bullet("Built automated onboarding workflows end-to-end: account provisioning, laptop imaging, "
        "SaaS access grants, and compliance verification - reducing new-hire IT setup from 2 days to under 4 hours")
    pdf.bullet("Designed and deployed a self-service knowledge base and support portal serving 200+ employees - "
        "decreased help desk ticket volume by enabling independent issue resolution "
        "(pattern aligned with AI-assisted support design)")
    pdf.bullet("Engineered access control audit system with automated monthly, weekly, and urgent review "
        "cycles across 30+ SaaS platforms - enforcing least-privilege across the org")
    pdf.bullet("Managed full SaaS platform lifecycle: evaluation, deployment, integration, access governance, "
        "and decommissioning for 30+ tools spanning clinical, administrative, and engineering functions")
    pdf.bullet("Led sprint planning and stakeholder reporting for IT initiatives using Agile methodology - "
        "bridging technical execution and business priorities across 8 different reporting structures")
    pdf.bullet("Automated endpoint fleet management for fully remote workforce - scripted imaging pipelines, "
        "configuration enforcement, and security baseline validation across macOS and Windows devices")
    pdf.bullet("Built internal tooling and scripts to eliminate repetitive IT operations tasks - "
        "Python and PowerShell automation for user provisioning, license auditing, and compliance reporting")

    pdf.job_header("Brooks Automation", "Apr 2022 - Jul 2022",
        "IT Support Technician")
    pdf.bullet("Administered Windows Server environments and managed endpoint deployments via SCCM and Dell KACE "
        "across two regulated manufacturing clean rooms")
    pdf.bullet("Managed nationwide Remedyforce ticket queue with SLA-driven prioritization and resolution")

    pdf.job_header("Matrix Global", "Sept 2021 - Mar 2022",
        "Desktop Support / Systems Deployment")
    pdf.bullet("Deployed and imaged systems at scale across hospital networks for an EHR rollout - "
        "automated imaging pipelines and asset tracking across clinical departments")
    pdf.bullet("Coordinated with clinical staff to minimize care disruption during hardware transitions")

    # PAGE 2
    pdf.section_heading("Projects & Open Source")

    pdf.job_header("Open Technology App", "opentechnologyapp.com", "Founder / Full-Stack Developer")
    pdf.bullet("Designed and shipped a production web application end-to-end - React/TypeScript frontend, "
        "Express backend, Supabase (Postgres) database, deployed on Vercel serverless infrastructure")
    pdf.bullet("Implements role-based access control with server-side enforcement, JWT authentication "
        "with 24-hour expiry, IP-based rate limiting, and strict CORS policy")
    pdf.bullet("Integrates AI tooling for workflow automation - task queue management with intelligent "
        "prioritization, automated status transitions, and webhook-driven automation rules")
    pdf.bullet("Built dashboard analytics system with configurable widgets: bar charts, progress tracking, "
        "Gantt views, and real-time stat cards pulling from live project data")
    pdf.bullet("Full CI/CD pipeline: GitHub integration, automatic deployment on push, environment "
        "variable management, and production monitoring")

    pdf.job_header("Open Technology Blog", "opentechnologyblog.com", "Author & Publisher")
    pdf.bullet("Writes applied AI, automation, and open-source content for technical practitioners - "
        "focused on practical implementation over theoretical discussion")
    pdf.bullet("Covers LLM integrations, prompt engineering patterns, workflow automation architectures, "
        "and AI-augmented IT operations with working code examples")
    pdf.bullet("Publishes guides on building production AI systems including tool integration, "
        "API design patterns, and deployment strategies for AI-powered applications")

    pdf.job_header("Job Application Automation Platform", "", "Developer")
    pdf.bullet("Built a multi-profile job scraping and automation tool using Python, Playwright, and "
        "15+ job board APIs - scrapes, filters by location/work type, and tracks applications end-to-end")
    pdf.bullet("Configurable per-user location filtering with radius-based matching, resume selection "
        "logic, and form auto-fill with regex pattern matching against application fields")
    pdf.bullet("Demonstrates practical AI/automation engineering: browser automation, API orchestration, "
        "data pipeline design, and multi-source aggregation with deduplication")

    pdf.section_heading("Technical Skills")
    pdf.skills_line("Languages & Frameworks: TypeScript, Python, React, Express, Node.js, SQL, REST APIs, HTML/CSS")
    pdf.skills_line("AI & Automation: LLM application design, Prompt engineering, Workflow automation, "
        "API integrations, Playwright browser automation, Python scripting, Data pipeline design")
    pdf.skills_line("Infrastructure: SaaS platform engineering, Supabase (Postgres), Vercel serverless, "
        "AWS (basic), Windows Server, SCCM, Cisco networking, Git/GitHub, CI/CD")
    pdf.skills_line("Security: JWT authentication, RBAC, Rate limiting, Access governance, CORS enforcement, "
        "Input validation, Endpoint security management")
    pdf.skills_line("Methods: Agile / Scrum, Six Sigma (in progress), Systems deployment at scale, "
        "Technical documentation, Stakeholder communication")

    pdf.section_heading("Education & Professional Development")
    pdf.edu_entry("Southern New Hampshire University", "BS Computer Science", "June 2022")
    pdf.edu_entry("Nashua Community College", "AS Computer Networking - Cisco curriculum", "May 2020")
    pdf.ln(1)
    pdf.skills_line("Six Sigma Green/Black Belt - in progress")
    pdf.skills_line("Continuous learning: LLM application architecture, prompt engineering patterns, "
        "AI agent design, and production ML/AI deployment strategies")

    out = Path("output/alex/resumes/Alex_Moody_AIEngineer_Resume_2page.pdf")
    pdf.output(str(out))
    print(f"  Generated: {out}")


# ===================================================================
# ALEX - Cybersecurity 2-page
# ===================================================================

def generate_alex_cyber_2page():
    pdf = ResumePDF()
    pdf.add_page()
    pdf.header_block("Alexander Moody",
        "(603) 943-0051  |  alexmoody1421@gmail.com  |  Nashua, NH  |  opentechnologyapp.com")

    pdf.section_heading("Professional Summary")
    pdf.summary_text(
        "IT security professional with hands-on access control governance, compliance auditing, "
        "and endpoint management experience in regulated, remote-first environments. 4 years enforcing "
        "least-privilege across 30+ SaaS platforms for a distributed healthcare organization. "
        "Cisco networking trained. Pursuing Security+ and NIST framework certifications.")

    pdf.section_heading("Experience")

    pdf.job_header("Eleanor Health", "July 2022 - Present",
        "Senior IT Support Associate - Access Control & Compliance")
    pdf.context_paragraph(
        "Sole IT security operations point for a 200-person fully remote behavioral health organization "
        "through 8 leadership transitions in 4 years. Maintained continuous compliance coverage and "
        "access governance without disruption despite constant organizational restructuring - "
        "self-directing security priorities and onboarding each new manager into existing protocols.")
    pdf.bullet("Designed and enforced multi-cadence access control audit cycles (monthly full review, "
        "weekly spot checks, urgent triggered reviews) across all SaaS platforms - implementing and "
        "maintaining least-privilege principles for 200+ remote users across 30+ tools")
    pdf.bullet("Built automated employee offboarding pipeline ensuring immediate access revocation across "
        "all systems on termination - zero-delay deprovisioning preventing orphaned account risk")
    pdf.bullet("Managed automated laptop deployment and secure baseline configuration for remote "
        "employees - ensuring endpoint compliance posture from day one of employment")
    pdf.bullet("Developed and maintained internal security runbooks and incident response documentation, "
        "supporting audit readiness and operational continuity across 8 leadership changes")
    pdf.bullet("Frontline security escalation point - triaging access anomalies, emergency offboarding, "
        "credential compromise response, and urgent provisioning changes")
    pdf.bullet("Conducted SaaS platform security assessments during evaluation phase - SSO/SCIM capability, "
        "data residency, encryption standards, and API security posture review")
    pdf.bullet("Applied Agile methodology to compliance and security projects, delivering iterative "
        "improvements to access governance workflows with sprint-based tracking")

    pdf.job_header("Brooks Automation", "Apr 2022 - Jul 2022",
        "IT Support Technician - Network & Endpoint Security")
    pdf.bullet("Responded to emergency network issues onsite at two regulated manufacturing clean rooms - "
        "high-stakes, time-sensitive environment analogous to critical infrastructure protection")
    pdf.bullet("Administered Windows Server environments and managed endpoint deployments via SCCM and Dell KACE "
        "with security baseline enforcement across distributed sites")
    pdf.bullet("Managed nationwide Remedyforce ticket queue - distributed, multi-site support with "
        "SLA-driven prioritization in regulated environment")

    pdf.job_header("Matrix Global", "Sept 2021 - Mar 2022",
        "Desktop Support - Healthcare Endpoint Deployment")
    pdf.bullet("Executed large-scale endpoint deployment across multiple Boston-area hospitals for an EHR "
        "rollout - secure imaging, asset tagging, and inventory management in HIPAA-adjacent environments")
    pdf.bullet("Maintained chain-of-custody asset tracking and secure handoff procedures across clinical locations")

    # PAGE 2
    pdf.section_heading("Security & Technical Skills")
    pdf.skills_line("Access Control: SaaS identity lifecycle management, Least-privilege enforcement, "
        "Multi-cadence audit programs, SSO/SCIM evaluation, Orphaned account prevention")
    pdf.skills_line("Endpoint Security: Remote fleet management, Secure imaging & provisioning, "
        "Configuration baseline enforcement, Automated deployment pipelines, macOS & Windows hardening")
    pdf.skills_line("Infrastructure: Windows Server administration, SCCM / Dell KACE, Network troubleshooting, "
        "Cisco networking (AS curriculum), Firewall fundamentals, VPN management")
    pdf.skills_line("Compliance & Governance: HIPAA awareness, Security documentation & runbooks, "
        "Incident response procedures, Vendor security assessment, Audit trail maintenance")
    pdf.skills_line("Scripting & Automation: Python, PowerShell, API integrations for access automation, "
        "Playwright browser automation, Automated compliance reporting")
    pdf.skills_line("Methods: Agile PM, Six Sigma (in progress), Risk assessment, Incident triage & escalation")

    pdf.section_heading("Projects")
    pdf.job_header("Open Technology App", "opentechnologyapp.com", "Founder / Developer")
    pdf.bullet("Production web application with security-first architecture: server-side role enforcement, "
        "JWT authentication with 24h expiry, IP-based rate limiting (10 failures / 15min lockout), "
        "strict CORS policy, and input validation on all endpoints")
    pdf.bullet("Implements zero-trust patterns: every request authenticated, every resource ownership-checked, "
        "no client-side role trust - demonstrates security engineering beyond IT operations")
    pdf.bullet("Built with defense-in-depth: session tokens in sessionStorage (not localStorage), "
        "server-side CORS origin checking, and rate limiting on all auth endpoints")

    pdf.job_header("Open Technology Blog", "opentechnologyblog.com", "Author")
    pdf.bullet("Technical content on security automation, access control patterns, and secure application design")

    pdf.section_heading("Education & Certifications")
    pdf.edu_entry("Southern New Hampshire University", "BS Computer Science", "June 2022")
    pdf.edu_entry("Nashua Community College", "AS Computer Networking - Cisco curriculum", "May 2020")
    pdf.ln(1)
    pdf.skills_line("Pursuing: CompTIA Security+, NIST Cybersecurity Framework training")
    pdf.skills_line("Six Sigma Green/Black Belt - in progress")
    pdf.skills_line("Cisco CCNA curriculum completed (AS program) - routing, switching, network security fundamentals")

    pdf.section_heading("Security Philosophy")
    pdf.context_paragraph(
        "Four years as the sole security operations person at a 200-person remote org taught me that "
        "security is a system, not a checklist. When you go through 8 managers in 4 years, you learn "
        "that security processes must be self-documenting, automated where possible, and resilient to "
        "personnel changes. Every audit cycle I built, every runbook I wrote, every automation I deployed "
        "was designed to survive my own departure. That mindset - build it so it runs without you - "
        "is what I bring to security engineering.")
    pdf.context_paragraph(
        "I also learned that the hardest part of security is not the technical controls - it is getting "
        "200 people to follow them. Security that slows people down gets bypassed. Security that works "
        "invisibly gets adopted. Every access governance workflow I designed was tested against one "
        "question: will a clinician with 15 minutes between patients actually follow this process? "
        "If the answer was no, I redesigned it until the answer was yes.")

    out = Path("output/alex/resumes/Alex_Moody_Cybersecurity_Resume_2page.pdf")
    pdf.output(str(out))
    print(f"  Generated: {out}")


# ===================================================================
# ALEX - Health IT 2-page
# ===================================================================

def generate_alex_healthit_2page():
    pdf = ResumePDF()
    pdf.add_page()
    pdf.header_block("Alexander Moody",
        "(603) 943-0051  |  alexmoody1421@gmail.com  |  Nashua, NH  |  opentechnologyapp.com")

    pdf.section_heading("Professional Summary")
    pdf.summary_text(
        "Health IT professional with 4 years supporting clinical and administrative operations "
        "in healthcare. Experienced in EHR deployments, SaaS access governance, onboarding automation, "
        "and self-service support design for clinical staff. Thrives in fast-paced, patient-care-driven "
        "environments where technology must work reliably every time.")

    pdf.section_heading("Experience")

    pdf.job_header("Eleanor Health", "July 2022 - Present",
        "Senior IT Support Associate - Healthcare Startup (200+ employees)")
    pdf.context_paragraph(
        "Primary IT operations lead for a fully remote behavioral health startup serving patients "
        "across multiple states. Maintained uninterrupted IT services through 8 management transitions "
        "in 4 years - self-directing clinical systems support, compliance processes, and technology "
        "rollouts to ensure patient care delivery was never impacted by internal organizational changes.")
    pdf.bullet("Designed and automated monthly, weekly, and urgent access control audits across all clinical "
        "SaaS platforms - reducing compliance risk, ensuring HIPAA-adjacent access hygiene, and eliminating "
        "manual review bottlenecks that previously delayed audit completion")
    pdf.bullet("Built automated onboarding and laptop deployment pipeline for clinical and administrative staff, "
        "cutting provisioning time from 2 days to under 4 hours - enabling new clinicians to begin seeing "
        "patients on their first day instead of waiting for IT setup")
    pdf.bullet("Created a comprehensive internal knowledge base enabling clinical staff to resolve common "
        "IT issues independently - reduced ticket volume and freed care teams to focus on patient outcomes")
    pdf.bullet("Served as primary IT liaison for a multi-site behavioral health organization, coordinating "
        "urgent technical escalations ensuring zero downtime for telehealth and patient-facing systems")
    pdf.bullet("Managed 30+ SaaS platforms spanning clinical (EHR integrations, telehealth), administrative "
        "(HR, finance), and communication tools - full lifecycle ownership from evaluation to sunset")
    pdf.bullet("Applied Agile project management to IT initiatives; leading sprint planning and "
        "stakeholder communications for technology rollouts across clinical and operational departments")
    pdf.bullet("Built emergency IT response procedures ensuring clinician access to patient systems was "
        "restored within minutes during outages - direct impact on continuity of care")

    pdf.job_header("Matrix Global", "Sept 2021 - Mar 2022",
        "Desktop Support - Hospital EHR Deployment")
    pdf.bullet("Executed desktop and printer deployment across multiple Boston-area hospitals as part of "
        "an Electronic Health Record system implementation - hands-on clinical environment experience")
    pdf.bullet("Managed automated imaging, asset tagging, and deployment scheduling across clinical departments, "
        "coordinating with hospital IT teams and department leads")
    pdf.bullet("Coordinated directly with hospital department leads and nursing staff to minimize disruption "
        "to patient care during hardware transitions - learned to operate within clinical workflow constraints")

    pdf.job_header("Brooks Automation", "Apr 2022 - Jul 2022",
        "IT Support Technician")
    pdf.bullet("Managed nationwide Remedyforce ticketing response for internal employees across regulated facilities")
    pdf.bullet("Resolved emergency network issues in regulated clean room environments - experience with "
        "high-stakes, compliance-sensitive IT operations applicable to healthcare settings")
    pdf.bullet("Administered Windows Server, SCCM, and Dell KACE for device deployment and management")

    # PAGE 2
    pdf.section_heading("Projects")
    pdf.job_header("Open Technology App", "opentechnologyapp.com", "Founder / Developer")
    pdf.bullet("Production web application with user management, role-based access, and workflow automation - "
        "built with healthcare-applicable patterns: audit trails, access control, compliance-ready architecture")
    pdf.bullet("Implements server-side role enforcement, session management, rate limiting, and input "
        "validation - security patterns directly transferable to healthcare IT systems")
    pdf.bullet("Task queue management with priority levels, status workflows, and automated transitions - "
        "mirrors clinical workflow management and patient tracking system patterns")

    pdf.job_header("Open Technology Blog", "opentechnologyblog.com", "Author & Publisher")
    pdf.bullet("Writes about IT operations, workflow automation, and technology implementation for "
        "practitioners in healthcare and enterprise environments")
    pdf.bullet("Bridges healthcare operations experience with emerging technology trends including "
        "AI-assisted support design, automation engineering, and clinical workflow optimization")

    pdf.section_heading("Core Competencies")
    pdf.skills_line("Clinical Systems: EHR deployment & support, SaaS access governance for clinical tools, "
        "Telehealth platform management, Clinical workflow automation, System uptime management")
    pdf.skills_line("Compliance & Security: HIPAA compliance awareness, Access audit programs, Security "
        "documentation & runbooks, Incident response procedures, Vendor security assessment")
    pdf.skills_line("Infrastructure: Windows Server, SCCM / Dell KACE, Endpoint management, Remote workforce "
        "support, Automated provisioning pipelines, Network troubleshooting, Cisco networking")
    pdf.skills_line("Development: Python, TypeScript, React, Express, REST APIs, Playwright automation, SQL")
    pdf.skills_line("Methods: Agile PM, Six Sigma (in progress), Stakeholder communication, "
        "Cross-functional coordination with clinical teams, Sprint planning & retrospectives")

    pdf.section_heading("Why Healthcare IT")
    pdf.context_paragraph(
        "I have spent the last four years making sure clinicians can focus on patients instead of fighting "
        "with technology. At Eleanor Health, every system I built, every automation I deployed, and every "
        "access audit I ran had one purpose: keep patient care running without interruption. When a "
        "telehealth platform goes down, a patient in crisis does not get seen. When onboarding takes two "
        "days, a new clinician sits idle while their caseload waits. I understand that healthcare IT is "
        "not about the technology - it is about the 200 people who depend on it to deliver care, and the "
        "patients on the other end who never see the infrastructure but feel it when it fails.")
    pdf.context_paragraph(
        "Eight managers in four years also taught me something specific to healthcare: clinical staff do "
        "not have time for IT disruptions. When I designed processes, I designed them for people who have "
        "15 minutes between patients, not 15 minutes to troubleshoot a login issue. Every self-service "
        "tool, every automated workflow, every runbook I created was built to respect the clinician's time "
        "because their time belongs to patients, not to IT.")

    pdf.section_heading("Education")
    pdf.edu_entry("Southern New Hampshire University", "BS Computer Science", "June 2022")
    pdf.edu_entry("Nashua Community College", "AS Computer Networking - Cisco curriculum", "May 2020")
    pdf.ln(1)
    pdf.skills_line("Six Sigma Green/Black Belt - in progress")
    pdf.skills_line("HIPAA compliance training  |  EHR deployment experience (hospital-scale)")

    out = Path("output/alex/resumes/Alex_Moody_HealthIT_Resume_2page.pdf")
    pdf.output(str(out))
    print(f"  Generated: {out}")


# ===================================================================
# MARCELLI - Care Coordinator / MAPS 2-page
# ===================================================================

def generate_marcelli_care_coord_2page():
    pdf = ResumePDF(accent_color=(0, 128, 128))
    pdf.add_page()
    pdf.header_block("Marcelli Bonilla",
        "Nashua, NH 03060  |  (603) 417-9827  |  marcelli5sos@gmail.com  |  Bilingual: English / Spanish")

    pdf.section_heading("Professional Summary")
    pdf.summary_text(
        "Compassionate healthcare professional with 7+ years of patient-facing experience in clinical "
        "and community health settings. Bilingual English/Spanish with proven ability to bridge language "
        "and cultural barriers in patient care. Skilled in patient outreach, care coordination, EHR "
        "management, and navigating patients through complex healthcare systems.")

    pdf.section_heading("Relevant Experience")

    pdf.job_header("Lamprey Health Care - Nashua, NH", "July 2024 - Present",
        "Patient Care Representative")
    pdf.context_paragraph(
        "Primary point of contact for patients at a Federally Qualified Health Center serving diverse, "
        "underserved communities. Leverages bilingual fluency and 6 years of direct care background "
        "to bridge clinical and administrative patient needs in a high-volume community health setting.")
    pdf.bullet("Serve as the primary contact for patients navigating access to care - scheduling appointments, "
        "processing referrals, and connecting patients with appropriate providers and services")
    pdf.bullet("Conduct proactive patient outreach and follow-up to ensure appointment adherence, reduce "
        "no-show rates, and maintain continuity of care for chronic disease management patients")
    pdf.bullet("Manage Athena EHR inbox and task buckets, coordinating care team communications and ensuring "
        "timely follow-through on clinical orders, lab results, and referral documentation")
    pdf.bullet("Provide bilingual (English/Spanish) support to patients and families, reducing barriers "
        "to healthcare access for non-English-speaking community members")
    pdf.bullet("Deliver culturally sensitive customer service to diverse patient populations including "
        "immigrant families, elderly patients, and individuals navigating insurance for the first time")
    pdf.bullet("Assist with care coordination tasks including referral tracking, insurance navigation, "
        "sliding-scale fee enrollment, and connecting patients to community health resources")
    pdf.bullet("Identify patients at risk of falling through care gaps and escalate to clinical team for "
        "follow-up - drawing on direct care instincts developed over 6 years at the bedside")

    pdf.job_header("Langdon Place of Nashua - Nashua, NH", "Feb 2021 - Feb 2024",
        "Licensed Nursing Assistant (LNA)")
    pdf.context_paragraph(
        "Provided comprehensive care coordination for residents in a skilled nursing facility with "
        "a specialization in memory care. Developed deep expertise in working with patients who cannot "
        "advocate for themselves and families navigating difficult care decisions.")
    pdf.bullet("Provided individualized care coordination for residents with Dementia and Alzheimer's, "
        "collaborating with interdisciplinary care teams on daily care plans and behavioral interventions")
    pdf.bullet("Monitored and documented vital signs, behavioral changes, and functional status - supporting "
        "care plan adjustments for medically complex patients and flagging early warning signs")
    pdf.bullet("Communicated with families and clinical staff in English and Spanish to ensure holistic, "
        "patient-centered support - often serving as informal interpreter during family conferences")
    pdf.bullet("Maintained accurate chart documentation using facility EHR systems, supporting care "
        "continuity across shift changes and provider transitions")
    pdf.bullet("Participated in care team meetings contributing direct-care observations that informed "
        "treatment plan modifications for high-acuity residents")

    pdf.job_header("Courville of Nashua - Nashua, NH", "Feb 2018 - Feb 2021",
        "Licensed Nursing Assistant (LNA)")
    pdf.bullet("Delivered person-centered direct care for senior residents including wound care, "
        "wellness monitoring, and daily living assistance across a 3-year tenure")
    pdf.bullet("Mentored and trained new LNA staff on care protocols, compassionate patient engagement, "
        "and documentation standards - recognized as a team leader within 18 months")
    pdf.bullet("Built trusting relationships with Spanish-speaking families, providing bilingual support "
        "that improved family engagement in care decisions and reduced communication barriers")
    pdf.bullet("Supported hospice and end-of-life care with sensitivity and dignity, coordinating with "
        "families and clinical teams during difficult transitions")

    # PAGE 2
    pdf.section_heading("Core Competencies")
    pdf.skills_line("Patient Outreach & Engagement  |  Care Coordination & Navigation  |  Bilingual English/Spanish")
    pdf.skills_line("EHR Management (Athena Health)  |  HIPAA Compliance  |  Motivational Interviewing Awareness")
    pdf.skills_line("Appointment Scheduling & Follow-Up  |  Community Health & FQHC Experience  |  Referral Tracking")
    pdf.skills_line("Medical Terminology  |  Interdisciplinary Team Collaboration  |  Cultural Competency")
    pdf.skills_line("Insurance Navigation & Eligibility  |  Trauma-Informed Communication  |  Patient Advocacy")
    pdf.skills_line("Sliding-Scale Fee Administration  |  Prior Authorization Support  |  De-escalation Techniques")

    pdf.section_heading("Why Care Coordination")
    pdf.context_paragraph(
        "Seven years of direct patient care taught me that the biggest barrier to good outcomes is not "
        "clinical - it is navigational. Patients miss appointments because they cannot find childcare. "
        "They skip medications because they do not understand the instructions in English. They fall "
        "through the cracks between referral and follow-up. I have seen this from the bedside as an LNA "
        "and from the front desk as a Patient Care Representative. I want to work in care coordination "
        "because I have already been doing the work informally - connecting patients to resources, "
        "translating for families, following up when someone does not show. A MAPS or outreach role "
        "lets me do this full-time and with real impact.")
    pdf.context_paragraph(
        "At Lamprey Health Care, I see patients every day who are one missed appointment away from a "
        "health crisis. The Spanish-speaking mother who does not understand her child's referral paperwork. "
        "The elderly patient who cannot navigate the insurance system alone. The person in recovery who "
        "needs someone to follow up when they miss their appointment. I am already that person for many "
        "of them - I want a role where that work is not extra, it is the job.")

    pdf.section_heading("Languages & Cultural Competency")
    pdf.bullet("Native-level fluency in English and Spanish - written and spoken, including medical terminology")
    pdf.bullet("Experience serving diverse communities including immigrant families, elderly patients, "
        "and individuals with limited English proficiency at a Federally Qualified Health Center")
    pdf.bullet("Comfortable navigating sensitive cultural dynamics around healthcare, mental health stigma, "
        "and family-centered decision-making in Latino/Hispanic communities")
    pdf.bullet("Trusted by patients and families as a cultural bridge between clinical systems and "
        "community needs - often the first person patients ask for by name")

    pdf.section_heading("Education & Licensure")
    pdf.edu_entry("Licensed Nursing Assistant (LNA)", "State of New Hampshire", "Licensed 2018")
    pdf.edu_entry("Nashua High School South", "High School Diploma", "May 2018")
    pdf.ln(1)
    pdf.skills_line("CPR/BLS Certified  |  Interested in: Community Health Worker (CHW) certification")
    pdf.skills_line("Dementia care training  |  HIPAA compliance training  |  EHR proficiency (Athena Health)")

    out = Path("output/marcelli/resumes/Marcelli_Bonilla_Care_Coordinator_MAPS_2page.pdf")
    pdf.output(str(out))
    print(f"  Generated: {out}")


# ===================================================================
# MARCELLI - Coding & Billing 2-page
# ===================================================================

def generate_marcelli_coding_billing_2page():
    pdf = ResumePDF(accent_color=(44, 62, 120))
    pdf.add_page()
    pdf.header_block("Marcelli Bonilla",
        "Nashua, NH 03060  |  (603) 417-9827  |  marcelli5sos@gmail.com  |  Bilingual: English / Spanish")

    pdf.section_heading("Professional Summary")
    pdf.summary_text(
        "Detail-oriented healthcare professional with front-end revenue cycle experience in a high-volume "
        "FQHC environment. Proficient in Athena Health EHR with hands-on experience in intake processing, "
        "insurance verification, and billing queue management. Combines 6 years of direct clinical "
        "experience as an LNA with patient access responsibilities for a holistic understanding of the "
        "care-to-billing workflow that most office-only staff lack.")

    pdf.section_heading("Relevant Experience")

    pdf.job_header("Lamprey Health Care - Nashua, NH", "July 2024 - Present",
        "Patient Care Representative")
    pdf.context_paragraph(
        "Front-end revenue cycle role in a Federally Qualified Health Center processing high patient volume "
        "daily. Handles the full intake-to-documentation workflow that feeds downstream coding and billing, "
        "with direct accountability for data accuracy that impacts claim acceptance rates.")
    pdf.bullet("Process patient intake, insurance verification, and account setup in Athena Health EHR - "
        "verifying coverage eligibility, copay amounts, and sliding-scale fee qualification for FQHC patients")
    pdf.bullet("Manage front-end revenue cycle tasks including Athena inbox/bucket work: charge entry queues, "
        "billing edits, task management, and documentation completion tracking")
    pdf.bullet("Coordinate scheduling and referral documentation to ensure accurate and complete visit records "
        "that support clean claim submission downstream")
    pdf.bullet("Apply HIPAA guidelines to all patient data handling, records management, and verbal "
        "communication - maintaining strict compliance in a high-traffic reception environment")
    pdf.bullet("Communicate with patients regarding account status, insurance questions, eligibility changes, "
        "and billing inquiries using bilingual (English/Spanish) skills to serve diverse populations")
    pdf.bullet("Identify and correct documentation errors, missing fields, and insurance mismatches before "
        "they reach billing - proactively reducing claim rejection risk at the point of entry")
    pdf.bullet("Process prior authorizations and coordinate with insurance companies for approval of "
        "specialist referrals, diagnostic procedures, and prescription medications")

    pdf.job_header("Langdon Place of Nashua - Nashua, NH", "Feb 2021 - Feb 2024",
        "Licensed Nursing Assistant (LNA)")
    pdf.context_paragraph(
        "Clinical documentation role in a skilled nursing facility. This experience provides direct "
        "understanding of what clinical documentation should contain - a perspective that strengthens "
        "coding accuracy when reviewing charts for billing purposes.")
    pdf.bullet("Maintained thorough and accurate clinical chart documentation for regulatory compliance - "
        "understanding the downstream billing impact of incomplete or vague clinical notes")
    pdf.bullet("Applied medical terminology in daily care documentation, supporting accurate coding readiness "
        "for wound care, vital sign monitoring, and ADL assistance records")
    pdf.bullet("Assisted with wound care and vital sign documentation, contributing to complete and billable "
        "care records with proper clinical detail for ICD-10 code justification")
    pdf.bullet("Understood the connection between clinical documentation accuracy and downstream "
        "reimbursement - saw firsthand how documentation gaps led to billing complications")

    pdf.job_header("Courville of Nashua - Nashua, NH", "Feb 2018 - Feb 2021",
        "Licensed Nursing Assistant (LNA)")
    pdf.bullet("Documented patient care activities and clinical observations in compliance with state and "
        "facility documentation standards across a 3-year tenure")
    pdf.bullet("Trained new staff on documentation protocols, care record accuracy, and proper medical "
        "terminology usage - building habits that support clean billing downstream")

    # PAGE 2
    pdf.section_heading("Core Competencies")
    pdf.skills_line("Athena Health EHR (Proficient)  |  Front-End Revenue Cycle  |  Insurance Verification & Eligibility")
    pdf.skills_line("Chart & Clinical Documentation  |  HIPAA Compliance  |  Medical Terminology (Clinical Background)")
    pdf.skills_line("Patient Account Management  |  Billing Inbox / Bucket Workflows  |  Prior Authorization Processing")
    pdf.skills_line("Bilingual English/Spanish  |  Sliding-Scale Fee Administration  |  Referral Documentation")
    pdf.skills_line("Data Entry Accuracy  |  Claim Rejection Prevention  |  Patient Communication & Education")

    pdf.section_heading("Professional Development")
    pdf.bullet("Pursuing CPC (Certified Professional Coder) certification through AAPC - currently studying "
        "ICD-10-CM, CPT, and HCPCS Level II coding systems through self-directed coursework")
    pdf.bullet("Actively building knowledge of diagnosis coding, procedure coding, and modifier usage "
        "through practice exams and coding scenario exercises")
    pdf.bullet("Studying denial management workflows including root cause analysis, appeal letter writing, "
        "and payer-specific billing requirements for commercial and government payers")
    pdf.bullet("Learning medical coding software and claim scrubbing tools beyond Athena to broaden "
        "technical capability across multiple revenue cycle platforms")
    pdf.bullet("Committed to completing accredited medical billing and coding program to formalize the "
        "revenue cycle knowledge built through years of front-line healthcare experience")
    pdf.bullet("Building understanding of E/M coding levels, documentation requirements for each level, "
        "and how clinical note quality directly impacts code selection and reimbursement rates")

    pdf.section_heading("Why Medical Coding & Billing")
    pdf.context_paragraph(
        "Working as an LNA, I saw how documentation gaps created problems downstream - missing vitals, "
        "incomplete wound care notes, vague activity descriptions. Now on the front desk at Lamprey Health "
        "Care, I see the other side: how those gaps turn into claim denials and lost revenue. I understand "
        "both the clinical and administrative sides of the care-to-billing pipeline. I want to move into "
        "coding and billing because I can catch the errors that people who have only worked in an office "
        "would miss - I know what the clinical documentation should say because I have written it myself. "
        "When I see a wound care claim with insufficient detail, I know exactly what is missing because "
        "I have performed and documented that care with my own hands.")
    pdf.context_paragraph(
        "Revenue cycle work at an FQHC also taught me that billing is not just about money - it is about "
        "keeping the doors open for patients who have nowhere else to go. Every clean claim means the "
        "health center can continue serving the community. Every denial I prevent means a patient does not "
        "get an unexpected bill. I bring both the clinical eye and the mission-driven motivation that "
        "this work requires.")

    pdf.section_heading("Education & Licensure")
    pdf.edu_entry("Nashua High School South", "High School Diploma", "May 2018")
    pdf.ln(1)
    pdf.skills_line("Licensed Nursing Assistant (LNA) - State of New Hampshire (Licensed 2018)")
    pdf.skills_line("CPR/BLS Certified  |  HIPAA Compliance Training")
    pdf.skills_line("Pursuing: CPC Certification (AAPC)  |  Medical Billing & Coding coursework")

    out = Path("output/marcelli/resumes/Marcelli_Bonilla_Coding_Billing_2page.pdf")
    pdf.output(str(out))
    print(f"  Generated: {out}")


# ===================================================================
# MARCELLI - Direct Care 2-page
# ===================================================================

def generate_marcelli_direct_care_2page():
    pdf = ResumePDF(accent_color=(128, 0, 128))
    pdf.add_page()
    pdf.header_block("Marcelli Bonilla",
        "Nashua, NH 03060  |  (603) 417-9827  |  marcelli5sos@gmail.com  |  Bilingual: English / Spanish")

    pdf.section_heading("Professional Summary")
    pdf.summary_text(
        "Dedicated Licensed Nursing Assistant with 6 years of hands-on direct care in long-term care "
        "and skilled nursing facilities. Expertise in dementia/Alzheimer's care, wound care, vital sign "
        "monitoring, and end-of-life support. Natural trainer and team leader who rose to mentoring "
        "new staff within 18 months of starting. Bilingual English/Spanish.")

    pdf.section_heading("Direct Care Experience")

    pdf.job_header("Langdon Place of Nashua - Nashua, NH", "Feb 2021 - Feb 2024",
        "Licensed Nursing Assistant (LNA)")
    pdf.context_paragraph(
        "Provided comprehensive daily care for seniors with complex medical needs in a skilled nursing "
        "facility. Specialized in memory care for residents with Dementia and Alzheimer's, developing "
        "trusted relationships with residents and families over a 3-year tenure. Recognized by nursing "
        "staff as a reliable, clinically observant caregiver who catches changes early.")
    pdf.bullet("Provided comprehensive daily living assistance and personal care to seniors with complex "
        "medical needs including mobility limitations, cognitive decline, and chronic conditions")
    pdf.bullet("Specialized in Dementia and Alzheimer's care - used de-escalation techniques, routine-based "
        "approaches, and individualized behavioral strategies to support resident dignity, safety, and "
        "quality of life during episodes of confusion or agitation")
    pdf.bullet("Performed vital sign assessment (BP, pulse, respiration, temperature, O2 saturation) "
        "and reported abnormal findings to nursing staff with clear, actionable documentation")
    pdf.bullet("Assisted licensed nurses with wound care procedures including dressing changes, wound "
        "measurement documentation, and infection monitoring with proper reporting protocols")
    pdf.bullet("Maintained accurate and timely chart documentation in compliance with state and facility "
        "regulations - contributing to care continuity across shift changes and provider handoffs")
    pdf.bullet("Collaborated closely with RNs, LPNs, and interdisciplinary care teams to support and "
        "modify individualized care plans based on daily observations and resident behavioral patterns")
    pdf.bullet("Managed care for high-acuity residents requiring frequent repositioning, fall prevention "
        "protocols, and specialized nutritional support including feeding assistance")

    pdf.job_header("Courville of Nashua - Nashua, NH", "Feb 2018 - Feb 2021",
        "Licensed Nursing Assistant (LNA)")
    pdf.context_paragraph(
        "First LNA role. Grew from new hire to lead trainer within 18 months. Developed core "
        "competencies in direct care while building reputation as a reliable, compassionate caregiver "
        "trusted by both residents and families across a diverse long-term care population.")
    pdf.bullet("Delivered daily personal care including bathing, grooming, mobility assistance, transfers, "
        "and nutritional support for senior, rehabilitation, and hospice residents")
    pdf.bullet("Monitored residents for changes in condition - behavioral shifts, appetite changes, skin "
        "integrity issues, pain indicators - and communicated urgent observations to charge nurses "
        "with specific, actionable detail")
    pdf.bullet("Performed wound care and assisted with repositioning schedules to prevent pressure injury "
        "development in bed-bound and mobility-limited residents")
    pdf.bullet("Led new hire orientation and hands-on training for incoming LNA staff, demonstrating "
        "care protocols, documentation standards, and compassionate communication techniques")
    pdf.bullet("Supported hospice and end-of-life care with sensitivity and dignity - providing comfort "
        "care, emotional support to families, and maintaining a calm presence during final hours")
    pdf.bullet("Built trusting, compassionate relationships with residents and families, including "
        "Spanish-speaking families who relied on bilingual support for care updates, treatment "
        "explanations, and comfort during difficult medical decisions")

    pdf.job_header("Lamprey Health Care - Nashua, NH", "July 2024 - Present",
        "Patient Care Representative")
    pdf.bullet("Transitioned clinical care instincts into patient access role - supports patient care through "
        "scheduling, access coordination, and EHR documentation while maintaining patient-first approach")
    pdf.bullet("Uses direct care background to identify patient needs beyond the administrative interaction - "
        "recognizing when a patient may need additional clinical support or community resources")

    # PAGE 2
    pdf.section_heading("Clinical Skills")
    pdf.skills_line("Vital Sign Assessment & Monitoring  |  Wound Care & Dressing Changes  |  Infection Monitoring")
    pdf.skills_line("Dementia & Alzheimer's Specialized Care  |  Behavioral De-escalation Techniques")
    pdf.skills_line("Hospice & End-of-Life Comfort Care  |  ADL Assistance & Personal Care  |  Fall Prevention")
    pdf.skills_line("Clinical Documentation & Charting  |  Repositioning & Pressure Injury Prevention")
    pdf.skills_line("Infection Control & Safety Protocols  |  New Staff Training & Mentorship")
    pdf.skills_line("Bilingual Patient & Family Communication  |  HIPAA Compliance  |  Nutritional Support")
    pdf.skills_line("Interdisciplinary Team Collaboration  |  EHR Documentation (Athena Health)")

    pdf.section_heading("What Sets Me Apart")
    pdf.context_paragraph(
        "I have cared for people at the end of their lives, held the hands of residents who could not "
        "remember their own names, and explained medical procedures to families in their native language "
        "when no one else could. Six years of LNA work across two facilities gave me clinical skills, "
        "but more importantly it gave me the instinct to notice when something is wrong before it becomes "
        "a crisis - a subtle change in behavior, a wound that is not healing right, a resident who "
        "suddenly stops eating. I bring reliability, empathy, and clinical awareness that only comes "
        "from years at the bedside.")
    pdf.context_paragraph(
        "I am the person families trust to care for their parents and grandparents. I am the person new "
        "hires shadow because the charge nurses know I will teach them right. I am the person who stays "
        "late when a resident is having a hard night because walking away is not in my nature. That is "
        "what six years of direct care builds - not just skills, but character.")
    pdf.context_paragraph(
        "Being bilingual in a healthcare setting is not just about translating words - it is about "
        "translating fear, confusion, and grief into understanding and comfort. When a Spanish-speaking "
        "family is sitting at their mother's bedside and the doctor's explanation does not make sense, "
        "I am the person who sits with them and makes sure they understand what is happening, what the "
        "options are, and that their feelings matter in the decision. That is care that goes beyond "
        "the clinical - it is human.")

    pdf.section_heading("Education & Licensure")
    pdf.edu_entry("Licensed Nursing Assistant (LNA)", "State of New Hampshire", "Licensed 2018")
    pdf.edu_entry("Nashua High School South", "High School Diploma", "May 2018")
    pdf.ln(1)
    pdf.skills_line("CPR/BLS Certified  |  Dementia Care trained  |  Wound Care competency verified")
    pdf.skills_line("HIPAA Compliance Training  |  Infection Control certification")
    pdf.skills_line("Interested in: LPN program  |  Specialized memory care certification")

    out = Path("output/marcelli/resumes/Marcelli_Bonilla_Direct_Care_2page.pdf")
    pdf.output(str(out))
    print(f"  Generated: {out}")


# ===================================================================
# NEW ALEX - IT Manager
# ===================================================================

def generate_alex_it_manager():
    pdf = ResumePDF(accent_color=(0, 100, 80))
    pdf.add_page()
    pdf.header_block("Alexander Moody",
        "(603) 943-0051  |  alexmoody1421@gmail.com  |  Nashua, NH  |  opentechnologyapp.com")

    pdf.section_heading("Professional Summary")
    pdf.summary_text(
        "IT operations leader with 4 years managing enterprise SaaS infrastructure, access governance, "
        "and automation for a 200-person distributed organization. Proven ability to maintain operational "
        "continuity and deliver projects through 8 leadership transitions without disruption. "
        "Builds systems that scale. Communicates up and across. Ships without being told.")

    pdf.section_heading("Management & Operations Experience")

    pdf.job_header("Eleanor Health", "July 2022 - Present",
        "Senior IT Support Associate - IT Operations Lead (de facto)")
    pdf.context_paragraph(
        "Functioned as the primary IT operations decision-maker for a fully remote behavioral health "
        "startup. Through 8 direct manager changes in 4 years, consistently owned IT strategy, vendor "
        "relationships, and cross-functional coordination - effectively operating as IT Manager without "
        "the title. Built every major IT system and process the organization runs on today.")
    pdf.bullet("Onboarded 8 successive managers into existing IT operations, maintaining institutional "
        "knowledge and process continuity across each leadership transition - wrote the documentation "
        "that made each handoff seamless", bold_prefix="Team Continuity: ")
    pdf.bullet("Served as IT liaison to HR, clinical operations, finance, and executive leadership - "
        "translating technical constraints into business language and securing buy-in for IT initiatives",
        bold_prefix="Stakeholder Management: ")
    pdf.bullet("Managed 30+ SaaS platform lifecycle end-to-end: needs assessment, vendor evaluation, "
        "procurement negotiation, deployment, SSO/SCIM integration, access governance, usage "
        "monitoring, and decommissioning", bold_prefix="SaaS Portfolio (30+ tools): ")
    pdf.bullet("Built automated onboarding pipeline (account provisioning, laptop imaging, access grants, "
        "compliance verification) - reduced setup time from 2 days to 4 hours, enabling new hires to be "
        "productive on day one", bold_prefix="Onboarding Automation: ")
    pdf.bullet("Designed and maintained multi-cadence access control audit program (monthly, weekly, urgent) "
        "enforcing least-privilege across the entire organization - zero compliance gaps",
        bold_prefix="Access Governance: ")
    pdf.bullet("Led sprint planning, stakeholder reporting, and iterative delivery using Agile methodology - "
        "managed project backlog, capacity planning, and retrospectives",
        bold_prefix="Agile Delivery: ")
    pdf.bullet("Created self-service knowledge base and support portal that reduced help desk ticket volume "
        "and freed staff time for strategic work", bold_prefix="Self-Service IT: ")
    pdf.bullet("Managed IT budget priorities and vendor negotiations across multiple SaaS contracts, "
        "identifying cost optimization opportunities and eliminating redundant tools",
        bold_prefix="Budget & Vendor: ")

    pdf.job_header("Brooks Automation", "Apr 2022 - Jul 2022",
        "IT Support Technician")
    pdf.bullet("Multi-site support across regulated manufacturing environments - Windows Server, SCCM, Dell KACE")
    pdf.bullet("Managed nationwide ticket queue with SLA-driven prioritization and resolution tracking")

    pdf.job_header("Matrix Global", "Sept 2021 - Mar 2022",
        "Desktop Support - Hospital EHR Deployment")
    pdf.bullet("Large-scale endpoint deployment across Boston-area hospitals - project coordination with "
        "clinical department leads, deployment scheduling, and asset management")

    # PAGE 2
    pdf.section_heading("Leadership Competencies")
    pdf.skills_line("IT Operations Management  |  SaaS Portfolio Lifecycle  |  Vendor Relationship Management")
    pdf.skills_line("Cross-Functional Stakeholder Communication  |  Agile Project Management  |  Budget Awareness")
    pdf.skills_line("Process Design & Documentation  |  Change Management Through Leadership Transitions")
    pdf.skills_line("Incident Escalation & Response  |  Team Onboarding & Knowledge Transfer  |  Strategic Planning")

    pdf.section_heading("Technical Skills")
    pdf.skills_line("SaaS Administration (30+ platforms)  |  Identity & Access Management  |  Endpoint Fleet Management")
    pdf.skills_line("Windows Server  |  SCCM / Dell KACE  |  Cisco Networking  |  Automation Engineering")
    pdf.skills_line("Python  |  TypeScript  |  React  |  Express  |  REST APIs  |  Supabase  |  Git/GitHub")

    pdf.section_heading("Key Achievements")
    pdf.bullet("Maintained zero compliance gaps in access governance across 30+ platforms for 200+ users "
        "through 4 years of continuous auditing - never a failed audit or missed review cycle")
    pdf.bullet("Reduced new-hire IT provisioning from 2 days to 4 hours through end-to-end automation - "
        "every new employee productive on day one since pipeline launch")
    pdf.bullet("Successfully onboarded 8 different managers without operational disruption - built "
        "documentation and handoff procedures that made each transition seamless")
    pdf.bullet("Eliminated redundant SaaS spend through portfolio rationalization - identified overlapping "
        "tools and consolidated where possible while maintaining functionality")

    pdf.section_heading("Projects")
    pdf.job_header("Open Technology App", "opentechnologyapp.com", "Founder / Developer")
    pdf.bullet("Shipped a production SaaS application end-to-end: React/TypeScript, Express API, Supabase, "
        "Vercel - demonstrates full-stack technical depth alongside management capability")
    pdf.bullet("Managed entire product lifecycle: requirements, architecture, development, deployment, "
        "operations, and user management")

    pdf.job_header("Open Technology Blog", "opentechnologyblog.com", "Author")
    pdf.bullet("Technical content on IT operations, automation, and leadership in distributed organizations")

    pdf.section_heading("Leadership Philosophy")
    pdf.context_paragraph(
        "Eight managers in four years taught me that good IT operations cannot depend on any single person - "
        "including the manager. Every system I built at Eleanor Health was designed to be self-documenting, "
        "auditable, and transferable. When a new manager arrived, I did not start over - I handed them a "
        "playbook. When processes needed to change, I ran them through sprints with measurable outcomes. "
        "The result: four years of uninterrupted operations despite constant leadership turnover. That is "
        "what IT management looks like when it is built on systems instead of heroics.")

    pdf.section_heading("Education")
    pdf.edu_entry("Southern New Hampshire University", "BS Computer Science", "June 2022")
    pdf.edu_entry("Nashua Community College", "AS Computer Networking - Cisco curriculum", "May 2020")
    pdf.ln(1)
    pdf.skills_line("Six Sigma Green/Black Belt - in progress")

    out = Path("output/alex/resumes/Alex_Moody_ITManager_Resume.pdf")
    pdf.output(str(out))
    print(f"  Generated: {out}")


# ===================================================================
# NEW ALEX - Technical Project Manager
# ===================================================================

def generate_alex_technical_pm():
    pdf = ResumePDF(accent_color=(100, 50, 150))
    pdf.add_page()
    pdf.header_block("Alexander Moody",
        "(603) 943-0051  |  alexmoody1421@gmail.com  |  Nashua, NH  |  opentechnologyapp.com")

    pdf.section_heading("Professional Summary")
    pdf.summary_text(
        "Technical project manager who builds and ships. 4 years delivering IT infrastructure, "
        "automation, and SaaS projects in healthcare. Founded and shipped a production web application "
        "solo. Agile practitioner. Six Sigma in progress. Thrives in ambiguity - maintained project "
        "delivery through 8 leadership transitions without missing a sprint.")

    pdf.section_heading("Project Delivery Experience")

    pdf.job_header("Eleanor Health", "July 2022 - Present",
        "Senior IT Support Associate - Project & Automation Lead")
    pdf.context_paragraph(
        "Owned the project lifecycle for every major IT initiative at a 200-person remote healthcare "
        "startup. Navigated 8 manager transitions in 4 years by maintaining clear project documentation, "
        "stakeholder alignment, and delivery cadence regardless of who was in charge. Each project below "
        "was scoped, planned, executed, and delivered under my ownership.")
    pdf.bullet("Scoped, designed, and delivered an end-to-end automated onboarding system - account "
        "provisioning, laptop imaging, SaaS access, compliance checks. Reduced new-hire setup from "
        "2 days to 4 hours. Delivered in 3 sprints with cross-functional buy-in from HR, clinical ops, "
        "and IT leadership.", bold_prefix="Onboarding Automation (3 sprints): ")
    pdf.bullet("Designed and implemented a multi-cadence access audit program (monthly full review, "
        "weekly spot checks, urgent triggered reviews) across 30+ SaaS platforms. Managed rollout, "
        "stakeholder training, documentation, and ongoing optimization. Zero compliance gaps since launch.",
        bold_prefix="Access Governance Program: ")
    pdf.bullet("Led requirements gathering from department leads, content creation from subject matter "
        "experts, and deployment of an internal support portal. Reduced help desk ticket volume. "
        "Managed content updates on a sprint cycle with contribution from 5 departments.",
        bold_prefix="Self-Service Knowledge Base: ")
    pdf.bullet("Audited, evaluated, and managed lifecycle of 30+ SaaS tools - procurement evaluation, "
        "integration planning, access governance setup, usage monitoring, and decommissioning. "
        "Coordinated with finance and department leads on contract decisions.",
        bold_prefix="SaaS Portfolio Rationalization: ")
    pdf.bullet("Managed sprint planning, async standups for remote team, stakeholder reporting, "
        "retrospectives, and backlog grooming across all concurrent projects using Agile methodology")
    pdf.bullet("Built project documentation templates and handoff procedures that survived 8 manager "
        "transitions - each new manager inherited a clear project backlog, status dashboard, and "
        "decision log without losing momentum")

    pdf.job_header("Matrix Global", "Sept 2021 - Mar 2022",
        "Desktop Support - Hospital EHR Deployment Project")
    pdf.bullet("Participated in large-scale EHR deployment project across multiple Boston-area hospitals - "
        "enterprise project coordination, clinical stakeholder management, and deployment scheduling")
    pdf.bullet("Coordinated deployment scheduling with clinical department leads to minimize patient care "
        "disruption - learned to manage technical projects within clinical workflow constraints")

    pdf.job_header("Brooks Automation", "Apr 2022 - Jul 2022",
        "IT Support Technician")
    pdf.bullet("Managed nationwide ticket queue with SLA tracking in regulated manufacturing environments")

    # PAGE 2
    pdf.section_heading("Shipped Products")
    pdf.job_header("Open Technology App", "opentechnologyapp.com", "Founder / Full-Stack Developer")
    pdf.bullet("Conceived, designed, built, and deployed a production web application from zero to live - "
        "managed the entire product lifecycle as a solo founder and developer")
    pdf.bullet("Stack: React/TypeScript, Express, Supabase, Vercel - made architecture decisions, "
        "managed technical debt, and shipped iteratively with continuous deployment")
    pdf.bullet("Demonstrates end-to-end project ownership: requirements definition, technical architecture, "
        "iterative development sprints, testing, deployment, and post-launch operations")
    pdf.bullet("Features include: multi-role user management, task queue workflows with automation rules, "
        "dashboard analytics with configurable widgets, and public intake portals")

    pdf.job_header("Job Application Automation Platform", "", "Developer / Project Owner")
    pdf.bullet("Scoped, architected, and built a multi-profile job scraping and automation tool from "
        "requirements through deployment - managed as a personal project with 2 active users")
    pdf.bullet("Integrated 15+ external APIs and browser automation scrapers - vendor evaluation, "
        "API capability assessment, error handling, and fallback planning for each data source")
    pdf.bullet("Configurable per-user profiles with location filtering, resume matching, and form auto-fill")

    pdf.job_header("Open Technology Blog", "opentechnologyblog.com", "Author")
    pdf.bullet("Technical writing on project delivery, AI automation, and IT operations leadership")

    pdf.section_heading("PM & Technical Skills")
    pdf.skills_line("Project Management: Agile / Scrum, Sprint planning & retrospectives, Stakeholder management, "
        "Requirements gathering, Backlog grooming, Capacity planning, Risk assessment")
    pdf.skills_line("Process: Six Sigma (in progress), Change management, Documentation design, "
        "Cross-functional coordination, Vendor evaluation & procurement")
    pdf.skills_line("Technical: Python, TypeScript, React, Express, REST APIs, SQL, SaaS administration, "
        "Automation engineering, Playwright, Git/GitHub, CI/CD")
    pdf.skills_line("Domain: Healthcare IT, HIPAA compliance, EHR systems, Remote workforce operations")

    pdf.section_heading("PM Philosophy")
    pdf.context_paragraph(
        "I have managed projects through 8 leadership transitions. That teaches you one thing fast: "
        "the project plan must be stronger than the org chart. If your documentation cannot onboard a "
        "new stakeholder in 30 minutes, it is not documentation - it is notes. If your sprint cadence "
        "depends on a specific manager being in the room, it will not survive their departure. I build "
        "projects that run on systems, not relationships. The relationships matter, but the system is "
        "what keeps delivery moving when everything else changes.")

    pdf.section_heading("Education")
    pdf.edu_entry("Southern New Hampshire University", "BS Computer Science", "June 2022")
    pdf.edu_entry("Nashua Community College", "AS Computer Networking - Cisco curriculum", "May 2020")
    pdf.ln(1)
    pdf.skills_line("Six Sigma Green/Black Belt - in progress")

    out = Path("output/alex/resumes/Alex_Moody_TechnicalPM_Resume.pdf")
    pdf.output(str(out))
    print(f"  Generated: {out}")


# ===================================================================
# NEW ALEX - SaaS Operations
# ===================================================================

def generate_alex_saas_ops():
    pdf = ResumePDF(accent_color=(200, 80, 0))
    pdf.add_page()
    pdf.header_block("Alexander Moody",
        "(603) 943-0051  |  alexmoody1421@gmail.com  |  opentechnologyblog.com  |  opentechnologyapp.com")

    pdf.section_heading("Professional Summary")
    pdf.summary_text(
        "SaaS operations engineer with 4 years managing 30+ platform integrations, identity lifecycle, "
        "and automation for a distributed healthcare organization. Builds production web applications "
        "and internal tooling. Bridges IT operations and software engineering - equally comfortable "
        "evaluating a vendor and writing the API integration.")

    pdf.section_heading("Experience")

    pdf.job_header("Eleanor Health", "July 2022 - Present",
        "Senior IT Support Associate - SaaS Operations & Platform Engineering")
    pdf.context_paragraph(
        "Managed the complete SaaS ecosystem for a 200-person fully remote organization. Owned platform "
        "evaluation, deployment, integration, identity management, and decommissioning across 30+ tools. "
        "Maintained full operational ownership through 8 management transitions in 4 years - the "
        "longest-tenured person in the IT function and the institutional knowledge holder for every system.")
    pdf.bullet("Managed end-to-end lifecycle of 30+ SaaS platforms: needs assessment with department "
        "leads, vendor evaluation against security and integration criteria, procurement negotiation, "
        "SSO/SCIM integration, access provisioning, ongoing usage monitoring, and sunset planning",
        bold_prefix="Platform Lifecycle (30+ tools): ")
    pdf.bullet("Designed automated identity lifecycle covering the full employee journey - provisioning "
        "on hire (accounts, access, devices), role-based access changes on transfer, and "
        "immediate deprovisioning across all platforms on termination with zero orphaned accounts",
        bold_prefix="Identity & Access Automation: ")
    pdf.bullet("Implemented least-privilege access governance with multi-cadence audit program: monthly "
        "full review, weekly spot checks on sensitive systems, and urgent triggered reviews for "
        "anomalies - serving 200+ remote users", bold_prefix="Access Governance: ")
    pdf.bullet("Built automated onboarding pipeline: account creation across all required platforms, "
        "laptop imaging with security baseline, SaaS access grants based on role, and compliance "
        "verification - 4-hour provisioning vs. prior 2-day manual process",
        bold_prefix="Onboarding Pipeline: ")
    pdf.bullet("Created self-service support portal and knowledge base reducing dependency on IT for "
        "common tasks - password resets, software requests, FAQ resolution",
        bold_prefix="Self-Service Platform: ")
    pdf.bullet("Managed endpoint fleet for fully remote workforce - automated imaging, configuration "
        "management, security baseline enforcement, and remote troubleshooting across macOS and Windows")
    pdf.bullet("Agile sprint delivery with stakeholder reporting across clinical, HR, finance, and "
        "executive teams - translating SaaS operations work into business-relevant updates")

    pdf.job_header("Brooks Automation", "Apr 2022 - Jul 2022",
        "IT Support Technician")
    pdf.bullet("Windows Server, SCCM, Dell KACE administration in regulated manufacturing environments")
    pdf.bullet("Nationwide ticket queue management with SLA-driven prioritization")

    pdf.job_header("Matrix Global", "Sept 2021 - Mar 2022",
        "Desktop Support - Healthcare Endpoint Deployment")
    pdf.bullet("Large-scale EHR deployment across hospital networks - imaging, asset management, "
        "clinical coordination, and deployment scheduling across multiple sites")

    # PAGE 2
    pdf.section_heading("Production Software")
    pdf.job_header("Open Technology App", "opentechnologyapp.com", "Founder / Full-Stack Engineer")
    pdf.bullet("Built and operates a production SaaS application: React/TypeScript frontend, Express API, "
        "Supabase (Postgres), deployed on Vercel serverless - full-stack ownership from architecture to ops")
    pdf.bullet("Implements JWT authentication, role-based access control with server-side enforcement, "
        "IP-based rate limiting, strict CORS, and input validation on all endpoints")
    pdf.bullet("Automation engine with configurable triggers and actions - webhook integrations, status "
        "transitions, and field-based rules that execute server-side on item updates")
    pdf.bullet("Full CI/CD: GitHub integration, automatic deployment on push, environment variable management, "
        "and production monitoring - operates the same toolchain used in enterprise SaaS")

    pdf.job_header("Job Application Automation Platform", "", "Developer")
    pdf.bullet("Multi-profile automation tool integrating 15+ job board APIs and Playwright browser automation - "
        "demonstrates API integration engineering at scale with error handling and rate limiting")
    pdf.bullet("Configurable per-user profiles, location filtering with radius matching, resume selection "
        "logic, and form auto-fill with regex pattern matching - production-grade internal tooling")
    pdf.bullet("Built data pipeline: scrape, deduplicate, filter, enrich with work-type detection, and "
        "output to structured CSV with approval workflows")

    pdf.job_header("Open Technology Blog", "opentechnologyblog.com", "Author")
    pdf.bullet("Technical content on SaaS architecture, API integrations, workflow automation, and "
        "platform engineering for technical practitioners")

    pdf.section_heading("Technical Skills")
    pdf.skills_line("SaaS Operations: Platform lifecycle management (30+ tools), SSO/SCIM integration, "
        "Identity provisioning & deprovisioning, Vendor evaluation & procurement")
    pdf.skills_line("Development: TypeScript, Python, React, Express, Node.js, REST APIs, SQL, "
        "Playwright, Git/GitHub, CI/CD pipelines")
    pdf.skills_line("Infrastructure: Supabase (Postgres), Vercel serverless, Windows Server, SCCM, "
        "Cisco networking, Endpoint fleet management, Configuration automation")
    pdf.skills_line("Security: Access governance & least-privilege enforcement, JWT auth, RBAC, "
        "Rate limiting, HIPAA awareness, Compliance auditing, Vendor security assessment")
    pdf.skills_line("Methods: Agile / Scrum, Six Sigma (in progress), Technical documentation, "
        "Stakeholder communication, Process design & optimization")

    pdf.section_heading("Operations Philosophy")
    pdf.context_paragraph(
        "Most organizations treat SaaS tools as individual purchases. I treat them as a platform. "
        "Every tool in the stack has an identity lifecycle, an access model, an integration surface, "
        "and a sunset plan. When you manage 30+ tools for 200 people through 8 management transitions, "
        "you learn that the only thing that scales is automation and documentation. Manual processes "
        "break when people leave. Automated processes break when assumptions change - and at least "
        "those failures are logged and fixable. I build SaaS operations the way I build software: "
        "version-controlled, testable, and designed to outlast any single person.")

    pdf.section_heading("Education")
    pdf.edu_entry("Southern New Hampshire University", "BS Computer Science", "June 2022")
    pdf.edu_entry("Nashua Community College", "AS Computer Networking - Cisco curriculum", "May 2020")
    pdf.ln(1)
    pdf.skills_line("Six Sigma Green/Black Belt - in progress")

    out = Path("output/alex/resumes/Alex_Moody_SaaSOperations_Resume.pdf")
    pdf.output(str(out))
    print(f"  Generated: {out}")


# ===================================================================
# ALEX - AI Training / Data Annotation
# ===================================================================

def generate_alex_ai_training():
    """Resume tailored to AI-training platforms (DataAnnotation, Outlier,
    Alignerr, xAI Tutor, etc.) — leads with writing quality, evaluation
    rigor, coding ability, and domain knowledge rather than IT ops."""
    pdf = ResumePDF(accent_color=(106, 76, 175))
    pdf.add_page()
    pdf.header_block("Alexander Moody",
        "(603) 943-0051  |  alexmoody1421@gmail.com  |  Remote (Nashua, NH, US)  |  opentechnologyblog.com")

    pdf.section_heading("Professional Summary")
    pdf.summary_text(
        "Technical writer and systems professional with a BS in Computer Science, 4 years of "
        "production IT/automation work, and a published technical blog. Daily hands-on experience "
        "evaluating LLM outputs, writing and refining prompts, and reviewing code in Python and "
        "TypeScript. Detail-oriented by trade - built and ran compliance audit programs where "
        "accuracy and consistent judgment against written rubrics were the entire job. Available "
        "20+ hours/week for AI training, annotation, and evaluation work.")

    pdf.section_heading("Relevant Skills for AI Training Work")
    pdf.skills_line("Writing & Evaluation: Technical writing (published blog), rubric-based quality "
        "review, clear rationale writing, proofreading, fact-checking against documentation")
    pdf.skills_line("Coding (for code-annotation queues): Python, TypeScript/JavaScript, React, "
        "Express/Node.js, SQL, REST APIs - reads, writes, debugs, and reviews production code")
    pdf.skills_line("AI Familiarity: Prompt engineering patterns, LLM response comparison and ranking, "
        "hallucination spotting, instruction-following evaluation, AI-assisted workflow design")
    pdf.skills_line("Domain Knowledge: IT operations, cybersecurity/access control, healthcare IT "
        "(HIPAA-aware), networking (Cisco curriculum), SaaS administration")
    pdf.skills_line("Work Habits: Fully remote for 4 years, self-directed through 8 manager changes, "
        "consistent daily output without supervision, meets written spec exactly")

    pdf.section_heading("Experience")

    pdf.job_header("Open Technology Blog", "opentechnologyblog.com",
        "Author & Publisher - Applied AI and Automation Writing")
    pdf.bullet("Writes long-form technical content on LLM integrations, prompt engineering patterns, "
        "and workflow automation - the same explain-your-reasoning writing AI training tasks require")
    pdf.bullet("Publishes working code examples with step-by-step explanations - practiced at judging "
        "whether a technical explanation is correct, complete, and clear")
    pdf.bullet("Edits own drafts against a consistent style standard - directly transferable to "
        "response-rating and rewrite tasks")

    pdf.job_header("Eleanor Health", "July 2022 - Present",
        "Senior IT Support Associate - Automation & Compliance Auditing")
    pdf.bullet("Ran multi-cadence access control audits across 30+ SaaS platforms - thousands of "
        "individual judgment calls per year against written criteria, with zero failed audits")
    pdf.bullet("Wrote the organization's IT knowledge base: hundreds of task-oriented articles for "
        "non-technical staff - practiced at judging clarity for a general audience")
    pdf.bullet("Built Python and PowerShell automation for provisioning, license auditing, and "
        "compliance reporting - comfortable reading unfamiliar code and spotting defects")
    pdf.bullet("Documented every process to survive personnel changes - precise, unambiguous "
        "instruction writing is a core skill, not an afterthought")

    pdf.job_header("Open Technology App", "opentechnologyapp.com", "Founder / Full-Stack Developer")
    pdf.bullet("Designed and shipped a production web app end-to-end: React/TypeScript frontend, "
        "Express backend, Postgres database - can evaluate code-generation outputs across the stack")
    pdf.bullet("Integrates AI tooling for workflow automation - hands-on experience with where "
        "LLM outputs go wrong in real applications")

    pdf.section_heading("Why I Fit AI Training Work")
    pdf.context_paragraph(
        "AI training work rewards three things: consistent judgment against a rubric, clear written "
        "rationales, and enough technical depth to catch subtle errors. My audit background is "
        "rubric-based judgment at scale. My blog is public evidence of my writing. My CS degree and "
        "production coding work cover the technical queues - including code review and debugging "
        "tasks that most annotators can't access. All work submitted is my own.")

    pdf.section_heading("Education & Availability")
    pdf.edu_entry("Southern New Hampshire University", "BS Computer Science", "June 2022")
    pdf.edu_entry("Nashua Community College", "AS Computer Networking - Cisco curriculum", "May 2020")
    pdf.ln(1)
    pdf.skills_line("Availability: 20+ hrs/week, flexible schedule incl. evenings/weekends  |  "
        "US-based (New Hampshire)  |  Reliable high-speed internet, dedicated home office")

    out = Path("output/alex/resumes/Alex_Moody_AITraining_Resume.pdf")
    pdf.output(str(out))
    print(f"  Generated: {out}")


# ===================================================================
# ALEX - Freelance / Contract IT
# ===================================================================

def generate_alex_freelance_it():
    """Freelance/contract IT resume — leads with the two live products
    (opentechnologyapp.com, opentechnologyblog.com) as proof of independent
    delivery, then frames the employment history as engagement outcomes."""
    pdf = ResumePDF(accent_color=(180, 100, 20))
    pdf.add_page()
    pdf.header_block("Alexander Moody",
        "(603) 943-0051  |  alexmoody1421@gmail.com  |  opentechnologyapp.com  |  opentechnologyblog.com")

    pdf.section_heading("Profile")
    pdf.summary_text(
        "Independent IT and automation professional who ships complete systems solo - and can "
        "prove it with two live products. Built and operates a production SaaS application "
        "(opentechnologyapp.com) and publishes applied technical content (opentechnologyblog.com). "
        "4 years as the sole IT operator for a 200-person company - the exact skill set of "
        "fractional IT: own everything, document everything, need no supervision. Available for "
        "contract, fractional, and project-based engagements.")

    pdf.section_heading("Services")
    pdf.skills_line("Workflow Automation - Python/API automations for onboarding, auditing, reporting, "
        "and data pipelines; eliminate the manual work your team does every week")
    pdf.skills_line("Web Application Development - full-stack builds (React/TypeScript, Express, "
        "Postgres) from requirements to deployed product with auth, roles, and CI/CD")
    pdf.skills_line("Fractional IT Operations - SaaS administration, identity/access management, "
        "onboarding/offboarding pipelines, and endpoint management for small teams without an IT hire")
    pdf.skills_line("Access Control & Compliance Audits - least-privilege reviews across your SaaS "
        "stack, documented runbooks, HIPAA-aware processes")

    pdf.section_heading("Featured Work (Live Products)")

    pdf.job_header("Open Technology App", "opentechnologyapp.com", "Founder / Sole Developer & Operator")
    pdf.context_paragraph(
        "A production SaaS application designed, built, deployed, and operated by one person - "
        "end-to-end proof of independent delivery.")
    pdf.bullet("Full stack: React/TypeScript frontend, Express API, Supabase (Postgres), deployed on "
        "Vercel serverless with GitHub-driven CI/CD - the same architecture I deliver for clients")
    pdf.bullet("Production-grade security built in: JWT authentication, server-side role-based access "
        "control, IP rate limiting, strict CORS, input validation on every endpoint")
    pdf.bullet("Automation engine with configurable triggers, webhook integrations, and dashboard "
        "analytics (charts, Gantt views, live stat cards) - complex features shipped solo")
    pdf.bullet("Operated in production: monitoring, environment management, incident response - "
        "I don't hand off and disappear; I know what running software costs")

    pdf.job_header("Open Technology Blog", "opentechnologyblog.com", "Author & Publisher")
    pdf.bullet("Applied AI, automation, and open-source content for technical practitioners - "
        "LLM integrations, prompt engineering patterns, and workflow automation with working code")
    pdf.bullet("Public evidence of communication skill: every engagement includes documentation "
        "your team can actually use after I leave")

    pdf.job_header("Job Application Automation Platform", "", "Developer")
    pdf.bullet("Multi-user automation tool integrating 15+ job board APIs with Playwright browser "
        "automation, matching engine, admin dashboard, and per-user configuration")
    pdf.bullet("Demonstrates rapid internal-tool delivery: API orchestration, data pipelines, "
        "deduplication, and a self-serve web UI - the kind of tooling teams pay agencies for")

    # PAGE 2
    pdf.section_heading("Engagement History")

    pdf.job_header("Eleanor Health", "July 2022 - Present",
        "Senior IT Support Associate - sole IT operator (200-person remote healthcare company)")
    pdf.context_paragraph(
        "Four years running IT single-handedly through 8 management transitions - functionally a "
        "long-term fractional IT engagement, delivered while employed in-house.")
    pdf.bullet("Built the automated onboarding pipeline (accounts, laptop imaging, SaaS access, "
        "compliance checks) - cut provisioning from 2 days to 4 hours")
    pdf.bullet("Administered 30+ SaaS platforms end-to-end: evaluation, procurement, SSO/SCIM "
        "integration, access governance, decommissioning")
    pdf.bullet("Designed multi-cadence access audits enforcing least-privilege org-wide - zero "
        "failed audits in 4 years, HIPAA-aware environment")
    pdf.bullet("Wrote the self-service knowledge base that cut help desk volume - documentation "
        "designed to outlive its author, the core freelance deliverable")

    pdf.job_header("Brooks Automation / Matrix Global", "2021 - 2022",
        "IT Support & Hospital EHR Deployment")
    pdf.bullet("Multi-site enterprise support (Windows Server, SCCM, Dell KACE) and large-scale "
        "hospital endpoint deployment - comfortable dropping into unfamiliar environments and delivering")

    pdf.section_heading("Technical Skills")
    pdf.skills_line("Development: TypeScript, Python, React, Express/Node.js, SQL, REST APIs, "
        "Playwright automation, Git/GitHub, CI/CD")
    pdf.skills_line("Infrastructure: Supabase (Postgres), Vercel serverless, Windows Server, SCCM, "
        "Cisco networking, macOS/Windows endpoint management")
    pdf.skills_line("AI & Automation: LLM application design, prompt engineering, API integrations, "
        "workflow automation, data pipelines")
    pdf.skills_line("Security & Compliance: Access governance, JWT/RBAC, rate limiting, HIPAA "
        "awareness, audit programs, security runbooks")

    pdf.section_heading("How I Work")
    pdf.context_paragraph(
        "Every engagement produces three things: the working system, the documentation to run it "
        "without me, and a handoff your team can actually follow. Four years of surviving 8 "
        "management transitions taught me to build for my own absence - which is exactly what "
        "you want from a contractor. Fixed-scope projects, fractional retainers, or hourly - "
        "remote from New Hampshire (US), overlap with all US time zones.")

    pdf.section_heading("Education")
    pdf.edu_entry("Southern New Hampshire University", "BS Computer Science", "June 2022")
    pdf.edu_entry("Nashua Community College", "AS Computer Networking - Cisco curriculum", "May 2020")

    out = Path("output/alex/resumes/Alex_Moody_FreelanceIT_Resume.pdf")
    pdf.output(str(out))
    print(f"  Generated: {out}")


# ===================================================================
# ALEX - IT + Automation Contractor (≤10 hrs/week)
# ===================================================================

def generate_alex_it_automation_contractor():
    """Capped-hours contractor resume — built for part-time retainers and
    small fixed-scope automation projects (max 10 hrs/week alongside
    full-time work). Distinct from the broader freelance resume: this one
    leads with the hour cap as a feature and packages small offerings."""
    pdf = ResumePDF(accent_color=(20, 110, 160))
    pdf.add_page()
    pdf.header_block("Alexander Moody",
        "(603) 943-0051  |  alexmoody1421@gmail.com  |  opentechnologyapp.com  |  opentechnologyblog.com")

    pdf.section_heading("Profile")
    pdf.summary_text(
        "IT + automation contractor taking part-time engagements up to 10 hours/week - "
        "retainers and small fixed-scope projects. The pitch: automation is the highest-leverage "
        "IT spend there is, and it doesn't need a full-time hire. I build the script, the "
        "integration, or the workflow once; it saves your team hours every week from then on. "
        "Proof of delivery is public - a production SaaS app (opentechnologyapp.com) and a "
        "technical blog (opentechnologyblog.com), both built and operated solo.")

    pdf.section_heading("What Fits in 10 Hours a Week")
    pdf.bullet("Automation sprints - one manual process scripted end-to-end (Python/PowerShell/"
        "API): report generation, data syncs between SaaS tools, license audits, employee "
        "onboarding/offboarding checklists", bold_prefix="Fixed scope: ")
    pdf.bullet("Ongoing IT/automation retainer - a set monthly block for the automation backlog, "
        "SaaS administration, access reviews, and 'can you script this?' requests",
        bold_prefix="Retainer: ")
    pdf.bullet("Workflow integrations - webhook and API glue between the tools you already pay "
        "for (Google Workspace, Slack, Jira, HR/EHR systems, spreadsheets)",
        bold_prefix="Integrations: ")
    pdf.bullet("Small internal tools - a focused web app (form + database + dashboard) that "
        "replaces the spreadsheet everyone is afraid to touch", bold_prefix="Micro-apps: ")

    pdf.section_heading("Proof of Work (Live, Public)")

    pdf.job_header("Open Technology App", "opentechnologyapp.com", "Founder / Sole Developer & Operator")
    pdf.bullet("Production SaaS built solo: React/TypeScript, Express, Postgres, serverless deploy, "
        "CI/CD - with JWT auth, role-based access, rate limiting, and an automation engine "
        "(configurable triggers, webhooks, scheduled actions)")
    pdf.bullet("Built and operated in the margins around a full-time job - direct evidence that "
        "capped-hours engagements still ship")

    pdf.job_header("Open Technology Blog", "opentechnologyblog.com", "Author & Publisher")
    pdf.bullet("Applied AI and automation content with working code - LLM integrations, prompt "
        "patterns, workflow automation architectures")

    pdf.job_header("Job Application Automation Platform", "", "Developer")
    pdf.bullet("Personal automation platform integrating 15+ job board APIs, browser automation, "
        "a matching engine, and an admin dashboard - the exact shape of internal tooling "
        "small teams need")

    pdf.section_heading("Day-Job Track Record (Why You Can Trust the Hours)")
    pdf.job_header("Eleanor Health", "July 2022 - Present",
        "Senior IT Support Associate - sole IT/automation operator, 200-person remote company")
    pdf.bullet("Automated onboarding end-to-end (accounts, imaging, SaaS access, compliance "
        "verification): 2 days of manual work became a 4-hour pipeline - the ROI model "
        "every engagement targets")
    pdf.bullet("Python/PowerShell automation for provisioning, license auditing, and compliance "
        "reporting across 30+ SaaS platforms")
    pdf.bullet("Multi-cadence access audits, zero failures in 4 years, HIPAA-aware environment - "
        "small-block recurring work delivered reliably is literally my job")
    pdf.bullet("Every system documented to run without me - contractors who leave good docs "
        "are the ones who get called back")

    pdf.section_heading("Technical Skills")
    pdf.skills_line("Automation: Python, PowerShell, REST APIs, webhooks, Playwright, cron/"
        "scheduled tasks, data pipelines, Zapier-style workflow design (built custom)")
    pdf.skills_line("Development: TypeScript, React, Express/Node.js, SQL, Supabase (Postgres), "
        "Vercel serverless, Git/GitHub, CI/CD")
    pdf.skills_line("IT Operations: SaaS administration (30+ platforms), identity & access "
        "management, Google Workspace, endpoint management, Windows Server, Cisco networking")
    pdf.skills_line("AI: LLM integrations, prompt engineering, AI-assisted workflow design")

    pdf.section_heading("Engagement Terms")
    pdf.context_paragraph(
        "Up to 10 hours/week, hourly or fixed-scope. Async-first (email/Slack/Loom) with "
        "scheduled calls as needed; evenings and weekends US-Eastern work fine. Every project "
        "ends with documentation and a handoff - you own everything I build. Remote from "
        "New Hampshire, US.")

    pdf.section_heading("Education")
    pdf.edu_entry("Southern New Hampshire University", "BS Computer Science", "June 2022")
    pdf.edu_entry("Nashua Community College", "AS Computer Networking - Cisco curriculum", "May 2020")

    out = Path("output/alex/resumes/Alex_Moody_ITAutomationContractor_Resume.pdf")
    pdf.output(str(out))
    print(f"  Generated: {out}")


# ===================================================================
# Main — run all, or a single resume via --only <key>
# ===================================================================

GENERATORS = {
    "alex-ai-engineer": generate_alex_ai_2page,
    "alex-cybersecurity": generate_alex_cyber_2page,
    "alex-health-it": generate_alex_healthit_2page,
    "alex-it-manager": generate_alex_it_manager,
    "alex-technical-pm": generate_alex_technical_pm,
    "alex-saas-ops": generate_alex_saas_ops,
    "alex-ai-training": generate_alex_ai_training,
    "alex-freelance-it": generate_alex_freelance_it,
    "alex-it-automation-contractor": generate_alex_it_automation_contractor,
    "marcelli-care-coord": generate_marcelli_care_coord_2page,
    "marcelli-coding-billing": generate_marcelli_coding_billing_2page,
    "marcelli-direct-care": generate_marcelli_direct_care_2page,
}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=sorted(GENERATORS),
                        help="Generate a single resume instead of all")
    args = parser.parse_args()

    if args.only:
        print(f"\nGenerating resume: {args.only}\n")
        GENERATORS[args.only]()
        print("\nDone! 1 PDF generated.")
    else:
        print("\nGenerating resumes...\n")
        for name, fn in GENERATORS.items():
            fn()
        print(f"\nDone! {len(GENERATORS)} PDFs generated.")
