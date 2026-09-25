"""
Seeds job_title_skills from regex rules (first matching rule wins).
Additive and idempotent: never deletes rows, never touches rows whose
source is 'manual' (hand-edited) unless overwrite_manual=True.
"""

import re
from sqlalchemy import text

DDL = """
CREATE TABLE IF NOT EXISTS job_title_skills (
    title_key  VARCHAR(150) PRIMARY KEY,
    title      VARCHAR(150) NOT NULL,
    skills     TEXT NOT NULL,
    source     VARCHAR(20) DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

# (regex, skills) -- ORDER MATTERS: first match wins, generic fallbacks last.
RULES = [
    # --- the company's own roles (IBM HR data set): checked first ---
    (r"research scientist", "Experimental design, laboratory research, data analysis, statistics, scientific writing, literature review, Python or R, regulatory standards (GLP)"),
    (r"laboratory technician", "Laboratory techniques, sample preparation, lab equipment operation and calibration, quality control, GLP, safety procedures, documentation, data recording"),
    (r"manufacturing director", "Manufacturing operations, production planning, GMP, quality management, lean / six sigma, supply chain, team leadership, budgeting"),
    (r"healthcare representative", "Healthcare / pharmaceutical sales, product knowledge, relationship building with physicians, territory management, CRM, negotiation, medical terminology, presentations"),
    (r"head of research|research director", "R&D strategy, scientific leadership, project and portfolio management, budgeting, regulatory affairs, team management, stakeholder communication, innovation"),
    (r"sales executive", "B2B sales, account management, negotiation, pipeline management, CRM (Salesforce), presentations, market analysis, customer relationship"),
    (r"sales representative", "Prospecting, customer service, product demonstrations, CRM, cold calling, negotiation, order processing, communication"),
    (r"hr specialist|human resources", "Recruitment, onboarding, employee relations, HR policies, labour law compliance, HRIS, payroll basics, communication"),
    (r"(r&d|sales|hr) (manager|director)|senior (r&d|sales|hr) manager", "Team leadership, people management, budgeting, performance management, strategic planning, stakeholder communication, reporting, problem solving"),

    # truncated titles in the source data
    (r"^copy$|copywriter|publishing copy", "Copywriting, editing, proofreading, SEO writing, brand voice, research, deadline management"),
    (r"^sub$|press sub", "Sub-editing, copy editing, headline writing, fact-checking, style guides, page layout, deadline management"),

    # IT
    (r"data scientist", "Python, machine learning, statistics, SQL, pandas, data visualization, model evaluation, Jupyter"),
    (r"database administrator", "SQL, PostgreSQL, database tuning, backup and recovery, data modeling, security, monitoring, ETL"),
    (r"games developer", "C++, C#, Unity, Unreal Engine, gameplay programming, 3D math, debugging, Git"),
    (r"multimedia", "JavaScript, HTML5, CSS, animation, Adobe Creative Suite, UI design, video editing, Git"),
    (r"applications developer|programmer, applications|systems developer|programmer, systems|software engineer", "Java, Python, C#, SQL, REST APIs, Git, unit testing, Agile, debugging, CI/CD"),
    (r"network engineer", "TCP/IP, routing and switching, Cisco, firewalls, VPN, network monitoring, troubleshooting, Linux"),
    (r"^it technical support|engineer, maintenance \(it\)", "Troubleshooting, Windows, Linux, hardware maintenance, networking, help desk, ticketing systems, scripting"),
    (r"^it consultant|systems analyst|information systems manager", "Requirements analysis, IT solution design, project management, SQL, process modeling, stakeholder communication, cloud basics, documentation"),
    (r"^it trainer", "Training delivery, curriculum design, MS Office, IT tools, presentation, coaching, assessment"),
    (r"^it sales|sales professional, it$", "B2B sales, IT solutions knowledge, CRM, lead generation, negotiation, presentations, account management"),
    (r"web designer", "HTML, CSS, JavaScript, Figma, responsive design, UX, WordPress, Photoshop"),
    (r"geographical information|cartographer", "GIS, ArcGIS, QGIS, spatial analysis, cartography, SQL, remote sensing, Python"),
    (r"data processing manager", "Data management, SQL, ETL, data quality, reporting, process optimization, team leadership"),
    (r"technical author", "Technical writing, documentation, Markdown, API documentation, editing, information architecture, research"),
    (r"animator|special effects", "2D and 3D animation, Maya, Blender, After Effects, compositing, storyboarding, motion design, visual storytelling"),
    (r"telecommunications researcher", "Telecom networks, 5G, signal processing, MATLAB, data analysis, research methods, technical writing"),
    (r"geophysic|seismolog|seismic", "Seismic data processing, geophysics, MATLAB, Python, signal processing, data quality control, Linux, report writing"),

    # armed forces, emergency and public safety
    (r"armed forces", "Leadership, planning and logistics, discipline, teamwork, decision making, physical fitness, security procedures, communication"),
    (r"diplomatic", "Diplomacy, international relations, foreign languages, negotiation, political analysis, report writing, cultural awareness"),
    (r"police officer|prison officer|immigration officer|probation officer|firefighter|ambulance|paramedic|emergency planning", "Emergency response, conflict management, first aid, risk assessment, report writing, legal procedures, communication, physical fitness"),

    # social, community, careers, education officers
    (r"social worker|youth worker|advice worker|adult guidance|learning mentor|community development|development worker|aid worker|international aid|volunteer coordinator", "Casework, safeguarding, active listening, needs assessment, interviewing, community engagement, report writing, communication"),
    (r"education officer|community education|community arts|careers", "Programme design, workshop delivery, guidance and coaching, public speaking, community engagement, evaluation, subject knowledge, communication"),

    # engineering
    (r"broadcast engineer|engineer, broadcasting", "Broadcast systems, audio and video signal chains, RF, live production, IP video, troubleshooting, equipment maintenance"),
    (r"aeronautical", "Aerodynamics, CAD, CFD, FEA, aircraft systems, MATLAB, aviation regulations, structural analysis"),
    (r"agricultural engineer|engineer, agricultural", "Agricultural machinery, irrigation systems, CAD, mechanical design, soil and water management, sustainability, project management"),
    (r"automotive", "Vehicle systems, CAD, powertrain, FEA, testing and validation, CAN bus, quality standards, MATLAB"),
    (r"biomedical engineer|engineer, biomedical", "Medical device design, CAD, ISO 13485, signal processing, testing, MATLAB, risk management"),
    (r"building services", "HVAC design, electrical services, AutoCAD, energy efficiency, building regulations, MEP coordination, project management"),
    (r"chemical engineer|engineer, chemical", "Process design, mass and energy balances, Aspen, process safety, thermodynamics, plant operations, quality control"),
    (r"civil engineer|engineer, civil|structural", "Structural analysis, AutoCAD, Civil 3D, construction management, geotechnics, building codes, surveying, project management"),
    (r"communications engineer|engineer, communications", "Telecom systems, RF engineering, networking, signal processing, fiber optics, testing, troubleshooting"),
    (r"control and instrumentation", "PLC, SCADA, instrumentation, control systems, automation, electrical drawings, calibration, troubleshooting"),
    (r"drilling|petroleum", "Drilling engineering, reservoir basics, well design, HSE, oil and gas operations, data analysis, cost estimation, project management"),
    (r"electrical|electronics", "Circuit design, AutoCAD Electrical, PLC, power systems, embedded systems, testing, safety standards, troubleshooting"),
    (r"energy engineer|engineer, energy|energy manager", "Energy auditing, renewable energy systems, energy modeling, sustainability reporting, data analysis, regulations, project management"),
    (r"engineering geologist|geologist, engineering", "Engineering geology, site investigation, geotechnics, geological mapping, GIS, ground modeling, report writing"),
    (r"engineer, land|land/geomatics|surveyor, land|hydrographic|^land$", "Land surveying, GNSS, total station, AutoCAD, GIS, cadastral mapping, bathymetry, data processing"),
    (r"manufacturing|production engineer|engineer, production|maintenance engineer|engineer, maintenance", "Lean manufacturing, process improvement, CAD, maintenance planning, quality control, Six Sigma, root cause analysis, PLC basics"),
    (r"materials engineer|engineer, materials|metallurgist", "Materials characterization, failure analysis, heat treatment, testing standards, microscopy, CAD, data analysis"),
    (r"mechanical", "Mechanical design, SolidWorks, CAD, FEA, thermodynamics, manufacturing processes, GD&T, prototyping"),
    (r"mining engineer|engineer, mining", "Mine planning, geology basics, Surpac, ventilation, blasting, safety regulations, cost estimation, project management"),
    (r"site engineer|engineer, site|contractor", "Site supervision, construction methods, setting out, AutoCAD, quality control, health and safety, contract management, reporting"),
    (r"technical sales engineer|engineer, technical sales", "Technical sales, product knowledge, solution engineering, CRM, presentations, negotiation, customer support"),
    (r"water engineer|engineer, water", "Hydraulics, water treatment, pipe network design, hydrology, AutoCAD, environmental regulations, project management"),
    (r"naval architect", "Ship design, hydrostatics, structural analysis, CAD, stability calculations, maritime regulations, CFD, project management"),

    # finance and business
    (r"actuary", "Actuarial modeling, statistics, probability, Excel, R or Python, risk assessment, financial mathematics, SQL"),
    (r"tax adviser|tax inspector|senior tax", "Tax law, tax compliance, tax planning, auditing, financial analysis, Excel, regulatory knowledge"),
    (r"accountant|accounting technician", "Financial reporting, bookkeeping, IFRS, tax compliance, auditing, Excel, accounting software, reconciliation"),
    (r"comptroller|financial controller|financial manager|corporate treasurer|pension", "Financial planning, budgeting, forecasting, internal controls, financial reporting, cash management, ERP, compliance"),
    (r"company secretary|secretary, company", "Corporate governance, company law, board administration, regulatory filings, compliance, minute taking, records management"),
    (r"trader|dealer", "Market analysis, trading platforms, risk management, derivatives, quantitative analysis, Excel, Bloomberg, regulatory compliance"),
    (r"banker|investment analyst", "Financial modeling, valuation, credit analysis, Excel, market research, client relationship management, Bloomberg, presentations"),
    (r"financial risk|risk manager", "Risk modeling, statistics, Excel, SQL, scenario analysis, regulatory compliance, VaR, reporting"),
    (r"financial planner|financial adviser", "Financial planning, investment advice, retirement planning, risk profiling, client relationship management, regulations, communication"),
    (r"insurance underwriter", "Risk assessment, underwriting guidelines, insurance products, data analysis, decision making, regulatory knowledge, negotiation"),
    (r"insurance account|insurance broker", "Insurance products, client relationship management, negotiation, sales, risk assessment, CRM, communication"),
    (r"claims|loss adjuster|insurance risk|surveyor, insurance", "Claims assessment, investigation, policy interpretation, loss estimation, negotiation, fraud detection, report writing, customer service"),
    (r"economist|statistician|operational researcher", "Statistics, econometrics, optimization, R or Python, SQL, modeling, data visualization, report writing"),
    (r"market researcher", "Survey design, SPSS, statistics, qualitative research, consumer insights, Excel, data visualization, report writing"),
    (r"management consultant", "Problem solving, business analysis, project management, stakeholder management, PowerPoint, data analysis, change management"),
    (r"media buyer|media planner", "Media planning, negotiation, audience analytics, ad platforms, budget management, campaign optimization, Excel, reporting"),
    (r"advertising account planner", "Consumer insights, market research, brand strategy, campaign planning, data analysis, creative briefing, presentation"),
    (r"advertising account executive|sales promotion account", "Client relationship management, campaign management, budgeting, presentations, project coordination, negotiation, communication"),
    (r"advertising art director", "Art direction, creative concepting, Adobe Creative Suite, branding, layout, team leadership, client presentation"),
    (r"marketing executive", "Digital marketing, SEO, social media, Google Analytics, content creation, campaign planning, email marketing, market research"),
    (r"public relations|public affairs", "Press releases, media relations, stakeholder engagement, crisis communication, campaign planning, copywriting, social media, event coordination"),
    (r"sales executive|medical sales", "B2B sales, CRM, lead generation, negotiation, presentations, account management, pipeline management, product knowledge"),
    (r"buyer|purchasing manager", "Procurement, supplier negotiation, contract management, inventory management, cost analysis, ERP, forecasting, sourcing"),
    (r"merchandiser", "Merchandising, visual display, inventory management, sales trend analysis, planograms, supplier coordination, retail analytics"),
    (r"retail manager|bookseller", "Store management, sales, inventory management, customer service, staff scheduling, merchandising, cash handling, KPIs"),
    (r"freight|air broker|ship broker", "Freight forwarding, customs documentation, logistics coordination, incoterms, shipping regulations, negotiation, ERP"),
    (r"logistics|warehouse|passenger transport|transport planner", "Supply chain management, inventory control, warehouse management systems, logistics planning, route optimization, KPIs, health and safety, ERP"),
    (r"quality manager", "Quality management systems, ISO 9001, auditing, root cause analysis, Six Sigma, statistical process control, documentation"),
    (r"production manager|print production", "Production planning, scheduling, lean manufacturing, quality control, budgeting, team leadership, health and safety, ERP"),
    (r"product manager", "Product roadmap, market research, Agile, user stories, stakeholder management, data analysis, prioritization"),
    (r"product/process|scientist, product", "R&D, experimental design, process optimization, lab techniques, statistics, technical reporting, quality standards"),
    (r"industrial/product|designer, industrial|product designer", "Product design, CAD, prototyping, sketching, 3D modeling, materials knowledge, user research"),

    # management, admin, hospitality, land-based
    (r"call centre|customer service manager", "Customer service, team leadership, call center KPIs, CRM, coaching, workforce scheduling, conflict resolution, reporting"),
    (r"facilities manager|office manager|records manager|information officer", "Office administration, facilities coordination, records management, MS Office, budgeting, vendor management, scheduling, communication"),
    (r"estate manager|land agent|estate agent", "Property valuation, estate management, property law, negotiation, tenant relations, contracts, market analysis, CRM"),
    (r"housing manager", "Housing law, tenant relations, property management, budgeting, community engagement, compliance, conflict resolution"),
    (r"health service manager", "Healthcare administration, budgeting, staff management, regulatory compliance, quality improvement, patient safety, data analysis"),
    (r"chief executive", "Strategic leadership, corporate governance, financial oversight, stakeholder management, decision making, change management, negotiation"),
    (r"chief financial", "Financial strategy, financial reporting, capital markets, risk management, budgeting and forecasting, M&A, regulatory compliance"),
    (r"chief marketing", "Marketing strategy, brand management, digital marketing, market analytics, team leadership, budget management, customer insight"),
    (r"chief operating", "Operations management, process optimization, strategic planning, budgeting, KPIs, supply chain, change management, leadership"),
    (r"chief strategy|chief of staff", "Corporate strategy, market analysis, business planning, competitive analysis, stakeholder management, financial modeling, executive communication"),
    (r"chief technology", "Technology strategy, software architecture, cloud, cybersecurity, engineering management, innovation, vendor management"),
    (r"personal assistant|secretary/administrator|^administrator$", "Calendar management, correspondence, MS Office, scheduling, filing, confidentiality, organization, communication"),
    (r"legal secretary", "Legal terminology, document preparation, dictation, calendar management, filing, confidentiality, MS Office, court procedures"),
    (r"medical secretary", "Medical terminology, patient records, appointment scheduling, dictation, confidentiality, MS Office, healthcare administration"),
    (r"charit|fundraiser|arts administrator|administrator, arts|arts development|sports administrator|administrator, sports|sports development", "Fundraising, grant writing, event coordination, budgeting, stakeholder engagement, volunteer coordination, project management, communication"),
    (r"civil service|local government|equality and diversity|race relations|recycling officer|waste management|trading standards|health and safety|environmental health|regulatory affairs", "Regulatory knowledge, compliance and auditing, policy analysis, inspection, risk assessment, report writing, stakeholder engagement, communication"),
    (r"politician|research officer|trade union|social research|intelligence analyst", "Research methods, data analysis, policy analysis, report writing, briefing papers, statistics, stakeholder engagement, critical thinking"),
    (r"human resources|personnel|recruitment consultant|training and development", "HR administration, recruitment, onboarding, employment law, HRIS, employee relations, training coordination, communication"),
    (r"hotel manager|accommodation manager|conference centre", "Hotel operations, guest services, booking systems, revenue management, team leadership, budgeting, health and safety, customer service"),
    (r"catering manager|restaurant manager|public house", "Food service operations, menu planning, food safety HACCP, staff management, cost control, inventory, customer service"),
    (r"barista", "Espresso preparation, customer service, POS operation, food safety, cash handling, teamwork, time management"),
    (r"event organiser|tour manager|holiday representative|travel agency", "Event and travel planning, budgeting, vendor management, logistics, client communication, booking systems, problem solving, languages"),
    (r"leisure centre|fitness centre|theme park|outdoor activities", "Facility operations, customer service, staff management, health and safety, first aid, budgeting, scheduling, marketing"),
    (r"tourism officer|tourist information|heritage manager", "Tourism promotion, visitor services, destination marketing, stakeholder relations, event coordination, funding applications, communication"),
    (r"farm manager|fish farm|forest|woodland|quarry", "Site and land operations, staff supervision, budgeting, health and safety, regulations, machinery, planning, environmental management"),

    # legal
    (r"barrister|solicitor|lawyer|legal executive|licensed conveyancer|patent attorney|trade mark attorney|patent examiner", "Legal research, drafting, advocacy, case management, contract law, client advice, negotiation, legal writing"),

    # media and creative
    (r"location manager|floor manager|stage manager|theatre manager|theatre director", "Production coordination, scheduling, budgeting, team communication, health and safety, negotiation, venue or stage management, problem solving"),
    (r"journalist", "Reporting, interviewing, news writing, fact-checking, editing, media law, research, deadline management"),
    (r"presenter", "On-air presentation, scripting, interviewing, voice control, improvisation, research, media knowledge, teamwork"),
    (r"producer", "Production planning, budgeting, scripting, scheduling, team coordination, editing oversight, negotiation, creativity"),
    (r"production assistant|broadcast assistant|runner|programme researcher", "Production support, scheduling, research, script coordination, communication, equipment handling, multitasking, teamwork"),
    (r"camera operator|photographer", "Camera operation, composition, lighting, Lightroom, Photoshop, equipment handling, video formats, storytelling"),
    (r"lighting technician|gaffer|best boy|sound technician", "Lighting or audio setup, equipment operation, rigging, electrical safety, mixing, set coordination, troubleshooting, teamwork"),
    (r"film/video editor|editor, film|video editor", "Video editing, Premiere Pro, DaVinci Resolve, color grading, sound editing, storytelling, workflow management"),
    (r"commissioning editor|editor, commissioning|features editor|editor, magazine|editorial assistant|proofreader|lexicographer|science writer|^writer$", "Editing, proofreading, writing, research, content planning, style guides, fact-checking, deadline management"),
    (r"publishing rights", "Rights licensing, contract negotiation, copyright law, royalty management, publishing knowledge, international sales, communication"),
    (r"translator|interpreter", "Bilingual proficiency, CAT tools, terminology research, proofreading, interpreting techniques, cultural knowledge, confidentiality"),
    (r"graphic designer|designer, graphic|illustrator", "Adobe Creative Suite, typography, layout, branding, illustration, color theory, Figma, client communication"),
    (r"fashion designer|designer, fashion|textile|clothing|garment", "Design sketching, pattern making, textiles and fabrics, trend forecasting, Adobe Illustrator, garment construction, quality control"),
    (r"conservator|conservation officer, historic|historic buildings", "Conservation techniques, restoration, materials science, condition reporting, documentation, heritage legislation, historical research, attention to detail"),
    (r"curator|archivist|archaeologist", "Collections management, cataloguing, research, exhibition planning, preservation, documentation, public engagement, writing"),
    (r"exhibition", "Exhibition design and planning, spatial layout, budgeting, logistics, installation coordination, CAD, project management, communication"),
    (r"furniture designer|designer, furniture|interior|set designer|designer, television|production designer", "Design sketching, CAD, SketchUp, space planning, model making, materials, color and lighting, client communication"),
    (r"jewellery|glass|ceramics|pottery|printmaker|fine artist|^artist$", "Craft techniques, drawing, materials knowledge, creativity, studio practice, portfolio development, exhibition, project planning"),
    (r"art gallery manager|gallery manager", "Gallery management, exhibition curation, art market knowledge, sales, client relations, marketing, event organization"),
    (r"^actor$|^dancer$|^musician$", "Performance, rehearsal discipline, script or score interpretation, stage presence, teamwork, physical or vocal control, audition skills, adaptability"),

    # education
    (r"lecturer|professor", "Lecturing, curriculum design, research, assessment, academic writing, mentoring, presentation, subject expertise"),
    (r"teacher|music tutor|private music", "Lesson planning, classroom management, assessment, curriculum knowledge, learner development, communication, differentiation, safeguarding"),
    (r"education administrator|administrator, education", "School administration, student records, scheduling, MS Office, budgeting, compliance, communication, organization"),
    (r"librarian", "Cataloguing, information retrieval, library management systems, research support, digital resources, classification, customer service"),

    # agriculture, horticulture, veterinary
    (r"veterinary", "Veterinary medicine, animal diagnosis, surgery, pharmacology, animal welfare, radiology, client communication"),
    (r"horticultural therapist|therapist, horticultural", "Therapeutic horticulture, client assessment, activity planning, plant knowledge, rehabilitation support, group facilitation, safeguarding, communication"),
    (r"horticultur|arboricultur|tree surgeon", "Plant science, pest and disease management, soil management, landscape maintenance, tree or crop care, advisory skills, group facilitation, health and safety"),
    (r"plant breeder|soil scientist|field trials|agricultural consultant|animal nutritionist|animal technologist", "Agronomy, field trial design, crop or animal science, data collection, statistics, sampling, regulations, report writing"),

    # health
    (r"neurosurgeon|surgeon", "Surgical technique, anatomy, patient assessment, aseptic technique, decision making, teamwork, postoperative care"),
    (r"doctor", "Clinical assessment, diagnosis, patient management, prescribing, medical records, communication, teamwork, evidence-based practice"),
    (r"dentist|oncologist|ophthalmologist|psychiatrist|pathologist|haematologist", "Clinical diagnosis, patient care, treatment planning, specialty medical knowledge, clinical documentation, multidisciplinary teamwork, communication, research"),
    (r"nurse|midwife|health visitor", "Patient care, clinical assessment, medication administration, documentation, infection control, safeguarding, communication, teamwork"),
    (r"pharmacist", "Dispensing, pharmacology, prescription checking, patient counselling, medication review, regulations, stock management"),
    (r"health promotion", "Health education, campaign design, community engagement, public health, evaluation, presentation, behavior change"),
    (r"clinical research", "Clinical trial monitoring, GCP, protocol compliance, source data verification, regulatory documentation, site management, data review"),
    (r"radiographer|audiological|physiological scientist|scientist, physiological|scientist, audiological", "Medical imaging or clinical measurement, patient positioning, equipment operation, radiation safety, image quality, patient care, documentation"),
    (r"sports coach|exercise physiologist|sports therapist|therapist, sports", "Coaching, fitness assessment, training programme design, injury prevention, first aid, performance analysis, motivation, communication"),
    (r"physiotherapist|occupational therapist|therapist, occupational|speech and language|chiropodist|podiatrist|chiropractor|osteopath|orthoptist", "Patient assessment, rehabilitation techniques, clinical reasoning, patient education, equipment operation, documentation, communication, evidence-based practice"),
    (r"optometrist|optician|acupuncturist|herbalist|phytotherapist|homeopath|dietitian|nutritional therapist|therapist, nutritional", "Patient consultation, assessment, treatment planning, health education, safety and ethics, record keeping, communication, evidence-based practice"),
    (r"psychiatric|psychologist|psychotherapist|counsell|therapist", "Psychological assessment, therapeutic techniques, case formulation, ethics, risk assessment, report writing, active listening, reflective practice"),
    (r"ergonomist|occupational hygienist", "Ergonomic assessment, workplace risk assessment, human factors, exposure monitoring, health and safety legislation, data analysis, report writing, training"),

    # science
    (r"medical physicist|physicist, medical|health physicist|radiation protection", "Radiation physics, dosimetry, radiation safety, quality assurance, regulations, statistics, monitoring instruments, report writing"),
    (r"laboratory technician|medical laboratory|medical technical officer|biomedical scientist|scientist, biomedical|biochemist|immunologist|microbiologist|cytogeneticist|geneticist|embryologist|histocompatibility|toxicologist|pharmacologist", "Laboratory techniques, sample analysis, quality control, laboratory safety, data recording, molecular or clinical assays, equipment maintenance, attention to detail"),
    (r"analytical chemist|chemist, analytical|forensic|geochemist|food technologist|brewing|technical brewer|colour technologist", "Chromatography, spectroscopy, laboratory analysis, method validation, quality control, sample preparation, data analysis, documentation"),
    (r"geologist|geoscientist|hydrologist|wellsite|mudlogger|minerals surveyor|surveyor, minerals|mining surveyor|surveyor, mining", "Geological mapping, field sampling, GIS, data interpretation, drilling or mining operations, HSE, report writing, modeling software"),
    (r"meteorologist|oceanographer|marine scientist|scientist, marine|astronomer", "Data analysis, Python or MATLAB, numerical modeling, remote sensing, statistics, field or observational research, scientific writing, GIS"),
    (r"ecologist|conservation officer|ranger|warden|fisheries|herpetologist|environmental consultant|environmental manager|water quality", "Ecological surveys, species identification, GIS, environmental regulations, data analysis, field work, report writing, impact assessment"),
    (r"scientist.*maths|scientist.*physical sciences|physicist", "Mathematical modeling, experimental design, Python or MATLAB, statistics, instrumentation, data analysis, scientific writing, problem solving"),
    (r"scientist.*life sciences|scientist.*medical|scientist, research|research scientist", "Molecular biology, laboratory techniques, experimental design, statistics, R or Python, literature review, scientific writing, data analysis"),

    # surveying, planning, architecture
    (r"quantity surveyor|surveyor, quantity", "Cost estimation, bills of quantities, contract administration, cost control, procurement, negotiation, Excel, construction knowledge"),
    (r"building control|building surveyor|surveyor, building|planning and development|commercial/residential|rural practice", "Property or building inspection, construction technology, planning law, valuation, report writing, AutoCAD, negotiation, regulations"),
    (r"town planner", "Urban planning, planning law, GIS, development control, community consultation, policy analysis, report writing, sustainability"),
    (r"architect", "Architectural design, AutoCAD, Revit, BIM, building regulations, sketching, project management, client communication"),

    # aviation and maritime
    (r"pilot|cabin crew|air traffic|merchant navy", "Aviation or maritime regulations, navigation, safety procedures, emergency response, crew coordination, situational awareness, communication, decision making"),

    # generic fallbacks (lowest priority)
    (r"engineer", "Engineering fundamentals, CAD, problem solving, technical documentation, project management, standards and regulations, mathematics, teamwork"),
    (r"scientist", "Laboratory techniques, experimental design, data analysis, statistics, scientific writing, research methods, health and safety, critical thinking"),
    (r"designer", "Design sketching, Adobe Creative Suite, creativity, client communication, trend research, prototyping, project management"),
    (r"manager", "Team leadership, budgeting, planning, performance management, stakeholder communication, reporting, problem solving, MS Office"),
]

_COMPILED = [(re.compile(p, re.IGNORECASE), s) for p, s in RULES]


def skills_for_title(title: str):
    """First matching rule wins; None if no rule matches."""
    for rx, skills in _COMPILED:
        if rx.search(title):
            return skills
    return None


def seed_job_title_skills(engine, overwrite_manual: bool = False, verbose: bool = True) -> dict:
    """Additive upsert. Never deletes. Rows with source='manual' are left
    untouched unless overwrite_manual=True."""
    updatable = "('llm', 'rules', 'manual')" if overwrite_manual else "('llm', 'rules')"
    upsert = text(f"""
        INSERT INTO job_title_skills (title_key, title, skills, source)
        VALUES (:k, :t, :s, 'rules')
        ON CONFLICT (title_key) DO UPDATE
            SET skills = EXCLUDED.skills, source = 'rules'
            WHERE job_title_skills.source IN {updatable}
        RETURNING (xmax = 0) AS inserted
    """)

    inserted = updated = kept = 0
    unmatched, seen = [], set()

    with engine.begin() as conn:
        conn.execute(text(DDL))
        rows = conn.execute(text(
            "SELECT DISTINCT trim(title) FROM job_postings WHERE title IS NOT NULL"
        )).fetchall()

        for title in sorted({r[0] for r in rows if r[0]}):
            key = title.lower()
            if key in seen:
                continue
            seen.add(key)

            skills = skills_for_title(title)
            if not skills:
                unmatched.append(title)
                continue

            row = conn.execute(upsert, {"k": key, "t": title, "s": skills}).fetchone()
            if row is None:
                kept += 1        # existing manual row, left untouched
            elif row[0]:
                inserted += 1
            else:
                updated += 1

    if verbose:
        print(f"job_title_skills: {inserted} inserted, {updated} updated, "
              f"{kept} kept (manual), {len(unmatched)} without rule (LLM fallback)")
        if unmatched:
            print("  No rule for:", ", ".join(unmatched[:20]), "..." if len(unmatched) > 20 else "")

    return {"inserted": inserted, "updated": updated, "kept": kept, "unmatched": unmatched}

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    from load import build_engine  # ETL's actual engine builder, in load.py
    engine = build_engine()
    seed_job_title_skills(engine)
    seed_job_title_skills(engine)