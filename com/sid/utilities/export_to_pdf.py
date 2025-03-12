import re
from fpdf import FPDF

# Function to clean text by replacing special characters
def clean_text(text):
    text = text.replace("’", "'")  # Replace curly apostrophe
    text = text.replace("“", '"').replace("”", '"')  # Replace curly quotes
    text = text.replace("–", "-")  # Replace en-dash
    text = text.replace("•", "-")  # Replace bullet points if any
    return text

# Create PDF instance
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_font("Arial", style='', size=12)

# Title
pdf.set_font("Arial", style='B', size=16)
pdf.cell(200, 10, clean_text("Online Personality Assessment - Sample Questions & Answers"), ln=True, align='C')
pdf.ln(10)

# Content
content = [
    ("Workplace Behavior", [
        ("How do you handle conflicts with teammates?",
         "I believe open communication is key to resolving conflicts. I try to understand the other person’s perspective and find a common ground. If needed, I involve a mediator or manager to ensure a fair resolution."),
        ("Do you prefer working independently or in a team?",
         "I am comfortable working both independently and in a team. While I enjoy collaborating with others to exchange ideas, I also take responsibility for my individual tasks to ensure efficiency."),
        ("How do you handle disagreements with your supervisor?",
         "I remain professional and communicate my perspective respectfully. If needed, I provide reasoning to support my viewpoint while staying open to feedback."),
        ("Describe a time when you had to adapt to a sudden change at work.",
         "In a previous project, the client changed requirements unexpectedly. I quickly reassessed the priorities, coordinated with my team, and adjusted our plan to meet the new expectations."),
        ("How do you handle working with a difficult coworker?",
         "I try to understand their perspective, maintain professionalism, and find ways to collaborate effectively. If necessary, I seek mediation from a manager to ensure a smooth workflow.")
    ]),
    ("Decision-Making & Problem-Solving", [
        ("If you have multiple deadlines approaching, how do you prioritize tasks?",
         "I assess the urgency and impact of each task, then prioritize based on deadlines and importance. I also break larger tasks into smaller steps and communicate with stakeholders if adjustments are needed."),
        ("What would you do if you receive unclear instructions from your manager?",
         "I would clarify the expectations by asking specific questions. If needed, I would seek guidance from colleagues or refer to past experiences to proceed efficiently."),
        ("Tell me about a time when you had to make a quick decision under pressure.",
         "During a production issue, I quickly analyzed logs, identified the root cause, and implemented a temporary fix to minimize downtime."),
        ("How do you handle conflicting priorities from different stakeholders?",
         "I assess the business impact and consult stakeholders to align expectations. If conflicts persist, I escalate to a manager for prioritization."),
        ("What steps do you take when facing a problem with no clear solution?",
         "I break down the problem, research potential solutions, seek advice from peers, and test different approaches before making a decision.")
    ]),
    ("Emotional Intelligence & Stress Handling", [
        ("How do you react when you receive negative feedback?",
         "I see feedback as an opportunity to improve. I listen carefully, analyze the points given, and work on making necessary changes. Constructive criticism helps me grow professionally."),
        ("How do you handle stress in a high-pressure work environment?",
         "I stay calm and focus on breaking down tasks into manageable steps. Prioritization, time management, and seeking help when necessary allow me to handle pressure effectively."),
        ("How do you manage your emotions when dealing with a frustrating situation at work?",
         "I practice self-awareness, take deep breaths, and focus on solutions rather than emotions."),
        ("Can you share an experience where you had to stay calm in a tense situation?",
         "During a high-stakes client presentation, unexpected technical issues arose. I calmly addressed the concerns, found a workaround, and successfully delivered the presentation."),
        ("How do you handle burnout or workplace fatigue?",
         "I manage workload effectively, take breaks when needed, and ensure work-life balance to maintain productivity and well-being.")
    ]),
    ("Leadership & Collaboration", [
        ("Have you ever taken initiative in a team project?",
         "Yes, in my previous projects, I proactively identified areas of improvement and proposed solutions. For instance, I suggested automating a repetitive task, which saved significant time for the team."),
        ("How do you motivate your team members?",
         "I ensure open communication, recognize their contributions, and provide support when needed. Encouraging a positive work environment and setting clear goals help in keeping the team motivated."),
        ("How do you encourage team members to contribute their ideas?",
         "I create an open and inclusive environment where everyone feels valued and heard. I encourage brainstorming and provide constructive feedback."),
        ("Describe a time when you had to mediate a conflict between team members.",
         "I facilitated a discussion where both parties could voice their concerns. By focusing on a common goal, we reached an agreement that satisfied both sides."),
        ("Have you ever had to step into a leadership role unexpectedly?",
         "Yes, when my team lead was unavailable, I took charge of task delegation and progress tracking to ensure smooth workflow.")
    ]),
    ("Ethical Dilemmas", [
        ("If you see a coworker violating company policy, what would you do?",
         "I would assess the severity of the situation and, if appropriate, address it directly with the coworker. If the issue is serious or affects the organization, I would report it to the relevant authority."),
        ("Would you report a mistake that no one noticed but could affect the project?",
         "Yes, I believe in maintaining integrity. I would bring it to my manager’s attention and suggest corrective actions to prevent potential issues."),
        ("How would you handle a situation where a coworker takes credit for your work?",
         "I would politely clarify my contributions in a professional manner and ensure my work is properly recognized in future collaborations."),
        ("What would you do if you discovered an ethical violation in your company?",
         "I would report the issue through the proper channels while ensuring confidentiality and adherence to company policies."),
        ("How do you balance honesty with workplace diplomacy?",
         "I maintain transparency while being tactful and professional in communication to preserve positive relationships.")
    ]),
    ("Self-Perception & Motivation", [
        ("How do you handle failure?",
         "I see failure as a learning experience. I analyze what went wrong, make improvements, and apply the lessons learned in future projects."),
        ("What motivates you to perform better at work?",
         "I am driven by a passion for learning, achieving goals, and making a meaningful impact. Recognition, growth opportunities, and challenging projects also keep me motivated."),
        ("What are your long-term career aspirations?",
         "I aim to take on leadership roles and contribute to innovative projects that drive business growth."),
        ("How do you ensure continuous personal and professional growth?",
         "I stay updated with industry trends, take relevant courses, and seek mentorship opportunities to enhance my skills."),
        ("What drives you to improve in your role?",
         "A commitment to excellence and a desire to make a meaningful impact push me to keep refining my skills.")
    ]),
    ("Additional Common Questions", [
        ("How would your colleagues describe you?",
         "They would describe me as a dependable and proactive team player who is always willing to help and take on challenges."),
        ("What would you do if a team member is not contributing effectively?",
         "I would first try to understand the reason behind their lack of contribution and offer support. If needed, I would discuss it with the team or manager to find a solution."),
        ("How do you adapt to change?",
         "I embrace change by staying flexible and open to new approaches. I quickly adjust by learning and applying new skills as needed."),
        ("What is your approach to handling constructive criticism?",
         "I welcome constructive criticism as a tool for improvement. I actively listen, analyze the feedback, and apply it to enhance my performance."),
        ("How do you ensure effective communication in a remote work setting?",
         "I maintain clear and frequent communication through digital tools, set expectations early, and schedule regular check-ins."),
        ("How do you handle situations where you have to say 'no' to a request?",
         "I assess the request's feasibility and provide a clear rationale if declining, while suggesting alternative solutions when possible.")
    ])
]

# Writing content to PDF
pdf.set_font("Arial", style='B', size=14)
for section, qa_pairs in content:
    pdf.cell(0, 8, clean_text(section), ln=True, align='L')
    pdf.ln(4)
    pdf.set_font("Arial", size=12)
    for question, answer in qa_pairs:
        pdf.set_font("Arial", style='B', size=12)
        pdf.multi_cell(0, 6, clean_text(f"Q: {question}"))
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 6, clean_text(f"A: {answer}"))
        pdf.ln(4)

# Save PDF
pdf_path = "C:/export/Personality_Assessment_Questions_Answers_v3.pdf"
pdf.output(pdf_path)

print(f"PDF successfully generated at: {pdf_path}")