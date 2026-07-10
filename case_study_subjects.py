# -*- coding: utf-8 -*-
"""
A curated bank of case-study subjects (companies and individual leaders),
seeded from John's "Cultures We'd Create" idea list. This exists because
agents/scout.py's case-study suggestions depend on live, grounded search
turning up a specific-enough subject on any given cycle -- it often will not.
When it does not, agents/strategist.py falls back to this bank instead of
skipping the case-study slot outright.

Each entry's research_notes is the actual descriptive text from John's list
(a real, sourced anchor), passed through to agents/case_study_writer.py the
same way a Scout headline would be -- so a bank-sourced case study is not
drafted from nothing, and the accuracy caveat in case_study_writer.py's
prompt still applies for anything beyond it.

Add more entries as John supplies them; there is no reason this list has to
stay fixed at its original 18.
"""

from pillars import PILLAR_NAMES

CASE_STUDY_SUBJECTS = [
    # --- Purpose-Driven Architecture -> governance itself reflects values,
    # a structural / systemic choice, not just a mission statement. ------
    {
        "subject": "Patagonia",
        "pillar": "Organizational Systems & Change Psychology",
        "category": "Purpose-Driven Architecture",
        "angle": "What changes in an organization's decisions once the "
                 "founder gives away ownership so profit structurally serves "
                 "a mission instead of shareholders.",
        "research_notes": (
            "Patagonia transferred ownership to a trust and a nonprofit "
            "collective so all profits combat climate change. Founder Yvon "
            "Chouinard's stated ethos: \"Earth is our only shareholder.\""
        ),
    },
    {
        "subject": "Ben & Jerry's",
        "pillar": "Organizational Systems & Change Psychology",
        "category": "Purpose-Driven Architecture",
        "angle": "What an independent social-mission board with veto power "
                 "over a corporate parent reveals about designing governance "
                 "to hold a mission under commercial pressure.",
        "research_notes": (
            "Ben & Jerry's is dual-structured: a for-profit company owned by "
            "Unilever, paired with an independent social mission board that "
            "can veto company decisions on ethical grounds."
        ),
    },
    {
        "subject": "Dr. Bronner's",
        "pillar": "Organizational Systems & Change Psychology",
        "category": "Purpose-Driven Architecture",
        "angle": "What a family-owned company's self-imposed executive pay "
                 "cap actually does to incentives and culture once it is a "
                 "structural rule rather than a values statement.",
        "research_notes": (
            "Dr. Bronner's is fully family-owned, caps executive pay, shares "
            "profits with workers, and advocates for fair-trade and "
            "regenerative agriculture."
        ),
    },

    # --- Human-Centered Leadership -> "wise leadership is relational
    # leadership" per the source list's own framing. ---------------------
    {
        "subject": "Southwest Airlines",
        "pillar": "Communication, Influence & Relational Leadership",
        "category": "Human-Centered Leadership",
        "angle": "How a founder's stated ordering of employees before "
                 "customers actually gets transmitted into a culture of "
                 "humor and empowerment, rather than staying a slogan.",
        "research_notes": (
            "Southwest Airlines' Herb Kelleher's philosophy: \"Take care of "
            "your employees, and they'll take care of your customers.\" "
            "Their culture remains one of humor, kindness, and empowerment."
        ),
    },
    {
        "subject": "The Container Store",
        "pillar": "Communication, Influence & Relational Leadership",
        "category": "Human-Centered Leadership",
        "angle": "What a company means when it says one well-trained, "
                 "cared-for employee is worth three average ones, and how "
                 "open-book pay transparency backs that claim operationally.",
        "research_notes": (
            "The Container Store is built around the \"1 = 3\" employee "
            "principle: one well-trained, cared-for employee is worth three "
            "average ones. Transparent pay and open-book management."
        ),
    },
    {
        "subject": "Barry-Wehmiller",
        "pillar": "Communication, Influence & Relational Leadership",
        "category": "Human-Centered Leadership",
        "angle": "What it takes to teach managers to see an employee as, in "
                 "the CEO's own phrase, \"someone's precious child\" -- and "
                 "whether that survives contact with a factory floor.",
        "research_notes": (
            "Barry-Wehmiller is led by Bob Chapman, who preaches \"Truly "
            "Human Leadership,\" teaching managers to see employees as "
            "\"someone's precious child.\" Their internal university trains "
            "leaders in empathy."
        ),
    },

    # --- Ethical Capitalism & Long-Term Thinking -> balancing financial
    # realism with moral ambition is a decision-architecture problem. ----
    {
        "subject": "Interface, Inc.",
        "pillar": "Strategic Thinking & Decision Architecture",
        "category": "Ethical Capitalism & Long-Term Thinking",
        "angle": "How a company in one of the dirtiest industries decided to "
                 "become regenerative, and what that decision required of "
                 "its strategy beyond a stated mission.",
        "research_notes": (
            "Interface, Inc. is a carpet manufacturer that transformed "
            "itself from one of the dirtiest industries into a regenerative "
            "enterprise (the \"Climate Take Back\" mission)."
        ),
    },
    {
        "subject": "Unilever (under Paul Polman)",
        "pillar": "Strategic Thinking & Decision Architecture",
        "category": "Ethical Capitalism & Long-Term Thinking",
        "angle": "What actually changes in a company's decisions when its "
                 "CEO removes quarterly earnings guidance to discourage "
                 "short-termism.",
        "research_notes": (
            "Unilever under Paul Polman used its global scale to argue "
            "sustainability and profitability are not opposites. Polman "
            "eliminated quarterly earnings guidance to discourage "
            "short-termism."
        ),
    },
    {
        "subject": "The Tata Group",
        "pillar": "Strategic Thinking & Decision Architecture",
        "category": "Ethical Capitalism & Long-Term Thinking",
        "angle": "What a century-old company can teach about designing "
                 "profit allocation itself around philanthropic obligation, "
                 "rather than treating giving as separate from strategy.",
        "research_notes": (
            "The Tata Group (India) is one of the oldest examples of "
            "ethical capitalism: over 60% of profits go to philanthropic "
            "trusts supporting education and social causes."
        ),
    },

    # --- Inclusive & Belonging-Oriented Cultures -> belonging as a design
    # principle of the org, not an HR initiative. -------------------------
    {
        "subject": "Salesforce",
        "pillar": "Team Dynamics & Culture Engineering",
        "category": "Inclusive & Belonging-Oriented Cultures",
        "angle": "What it means to build a company culture around a family "
                 "metaphor at Salesforce's scale, and whether the 1-1-1 "
                 "giving model changes how employees actually work.",
        "research_notes": (
            "Salesforce's \"Ohana\" culture is rooted in family and "
            "inclusivity; it dedicates 1% of equity, products, and employee "
            "time to philanthropy through the 1-1-1 model."
        ),
    },
    {
        "subject": "REI Co-op",
        "pillar": "Team Dynamics & Culture Engineering",
        "category": "Inclusive & Belonging-Oriented Cultures",
        "angle": "What changes in a company's incentives when its customers "
                 "are literally its shareholders, illustrated by its choice "
                 "to close on the industry's biggest sales day.",
        "research_notes": (
            "REI Co-op has a member-owned structure where customers are "
            "literally shareholders; it closed stores on Black Friday to "
            "encourage time in nature (\"Opt Outside\")."
        ),
    },
    {
        "subject": "Kickstarter",
        "pillar": "Team Dynamics & Culture Engineering",
        "category": "Inclusive & Belonging-Oriented Cultures",
        "angle": "What re-incorporating as a Public Benefit Corporation "
                 "actually commits a company to, beyond the announcement.",
        "research_notes": (
            "Kickstarter re-incorporated as a Public Benefit Corporation to "
            "balance stakeholder interests over shareholder primacy."
        ),
    },

    # --- Wisdom Through Experimentation -> systems that metabolize
    # feedback and change, not individual talent. -------------------------
    {
        "subject": "Pixar",
        "pillar": "Organizational Systems & Change Psychology",
        "category": "Wisdom Through Experimentation",
        "angle": "How a system for candid, hierarchy-blind feedback "
                 "changes what a creative organization is capable of "
                 "producing, versus relying on individual genius.",
        "research_notes": (
            "Pixar's \"braintrust\" model encourages open, candid feedback "
            "from peers regardless of hierarchy. Creativity is treated as "
            "communal, not individual genius."
        ),
    },
    {
        "subject": "IDEO",
        "pillar": "Organizational Systems & Change Psychology",
        "category": "Wisdom Through Experimentation",
        "angle": "What it takes to build a culture where curiosity and "
                 "iterative learning are the actual operating system, not a "
                 "value on a wall.",
        "research_notes": (
            "IDEO is a design firm known for human-centered innovation; its "
            "culture is built around curiosity, iterative learning, and "
            "psychological safety."
        ),
    },
    {
        "subject": "Spotify",
        "pillar": "Organizational Systems & Change Psychology",
        "category": "Wisdom Through Experimentation",
        "angle": "What the \"squad\" model actually trades off between "
                 "autonomy and accountability at scale.",
        "research_notes": (
            "Spotify runs an agile, team-based culture that prizes autonomy "
            "and mastery. Its \"squad\" model fosters both freedom and "
            "accountability."
        ),
    },

    # --- Modern Moral Leaders -> individual leaders as the unit of
    # analysis; moral courage and inner work under real pressure. ---------
    {
        "subject": "Satya Nadella",
        "pillar": "Self-Mastery & Executive Psychology",
        "category": "Modern Moral Leaders",
        "angle": "What it actually took, psychologically, to reorient a "
                 "once-toxic culture around empathy and a growth mindset "
                 "from the inside.",
        "research_notes": (
            "Satya Nadella reshaped Microsoft's culture around empathy, "
            "collaboration, and growth mindset, turning a once-toxic "
            "culture into one of trust and curiosity."
        ),
    },
    {
        "subject": "Rose Marcario",
        "pillar": "Self-Mastery & Executive Psychology",
        "category": "Modern Moral Leaders",
        "angle": "What it costs a CEO, personally, to keep a company "
                 "politically courageous and mission-driven while also "
                 "keeping it profitable.",
        "research_notes": (
            "Rose Marcario, former CEO of Patagonia, led the company "
            "through its most mission-driven years while keeping it "
            "profitable and politically courageous."
        ),
    },
    {
        "subject": "Dan Price",
        "pillar": "Self-Mastery & Executive Psychology",
        "category": "Modern Moral Leaders",
        "angle": "What actually happened, operationally and psychologically, "
                 "after a CEO cut his own pay to raise every employee to a "
                 "$70K minimum -- not just the headline decision.",
        "research_notes": (
            "Dan Price (Gravity Payments) famously cut his own pay to raise "
            "all employees to a $70K minimum salary; despite controversy, "
            "retention and productivity soared."
        ),
    },
]

# Fail loudly at import time if a future edit mistypes a pillar name -- this
# module is a fallback path that should never itself be the reason a case
# study can't be planned.
for _entry in CASE_STUDY_SUBJECTS:
    assert _entry["pillar"] in PILLAR_NAMES, (
        "case_study_subjects.py: unknown pillar %r for subject %r"
        % (_entry["pillar"], _entry["subject"])
    )


def used_subjects(history: list) -> set:
    """Subject names already covered by a published case study, per
    memory/content_history.json. Older entries predating subject tracking
    simply have no 'subject' key and are ignored, not treated as used."""
    return {e.get("subject") for e in history
            if e.get("format") == "case_study" and e.get("subject")}


def pick_subject(pillar: str, history: list) -> dict:
    """Pick the next bank entry to draft: prefer one not yet published,
    matching the given pillar; then any pillar; then, if every entry has
    been used, recycle from the top rather than refuse to plan a slot.
    Returns None only if the bank itself is empty."""
    if not CASE_STUDY_SUBJECTS:
        return None
    used = used_subjects(history)
    fresh = [s for s in CASE_STUDY_SUBJECTS if s["subject"] not in used]
    pool = fresh or CASE_STUDY_SUBJECTS
    for want_pillar in (pillar, None):
        for entry in pool:
            if want_pillar is None or entry["pillar"] == want_pillar:
                return entry
    return None
