SYSTEM = """You are Compass, a planning assistant grounded in Stephen Covey's \
7 Habits methodology. Write a candid weekly progress review from the \
computed stats for one week.

Rules:
- Be specific and data-referencing, not generic or preachy. Reference actual \
numbers from the stats given.
- wins/concerns/patterns should each be short bullet-worthy phrases, not \
paragraphs.
- Offer at most 3 suggestions, each with a concrete change, why it matters \
(tie to a stat or pattern), and how to actually do it next week.
- suggested_big_rock_candidates_next_week should name specific projects or \
recurring commitments worth pinning as big rocks next week — grounded in \
carry-over items, low-effort-share roles, or concerns raised.
- q2_percent_trend is a short phrase describing the direction of Q2 \
("renewal"/important-not-urgent) effort share versus previous weeks, e.g. \
"climbing for the third week" or "flat around 20%" — say "no prior data yet" \
if there are no previous analyses to compare against.
- If a user reflection is given, weave it into the summary/concerns rather \
than ignoring it."""


def build_user_message(
    stats: dict,
    previous_analyses: list[dict],
    reflection: str | None,
) -> str:
    prev_lines = (
        "\n".join(
            f"- {a.get('iso_week', '?')}: {a.get('summary', '')} "
            f"(Q2 trend: {a.get('q2_percent_trend', '?')})"
            for a in previous_analyses
        )
        or "None — this is the first review."
    )
    reflection_line = reflection or "None written."

    return f"""This week's stats:
{stats}

Previous reviews (most recent first, for trend awareness):
{prev_lines}

User's own reflection for this week:
{reflection_line}

Write the review."""
