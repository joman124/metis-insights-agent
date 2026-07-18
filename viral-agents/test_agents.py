# -*- coding: utf-8 -*-
"""
Unit tests for the parts of the Metis agents that run without an API key:
the Orchestrator's keyword routing, the pure-logic engagement critic, the
rule-based guardrail checks, and the video curator's pure helpers (candidate
selection, credit line, post assembly). These never call Gemini.

Run:  python -m unittest test_agents
  or: python test_agents.py
"""

import unittest

from agents.orchestrator import route
from agents.video_curator import select_top, build_post, _credit_line
import engagement
import guardrails
from metis_voice_profile import PLATFORM_RULES

VIRAL = PLATFORM_RULES["linkedin_viral"]
NOTE = PLATFORM_RULES["substack_note"]

EM_DASH = chr(0x2014)
CURLY_APOS = chr(0x2019)
EMOJI = chr(0x1F600)

GOOD_POST = (
    "Most AI pilots die between the demo and the workflow.\n"
    "A leadership team can approve one and never change how the work runs.\n"
    "The tool ships. The behavior does not.\n"
    "Measure the workflow, or you measured nothing.\n"
    "#Leadership #AI #FutureOfWork"
)


class TestRouting(unittest.TestCase):
    def test_intents(self):
        cases = {
            "post a viral video about AI agents": ("video", "AI agents"),
            "share a clip about the new model": ("video", "the new model"),
            "go viral about AI layoffs": ("viral", "AI layoffs"),
            "react to the earnings call": ("viral", "the earnings call"),
            "what's trending?": ("trending", None),
            "hello there": ("unknown", None),
        }
        for request, expected in cases.items():
            self.assertEqual(route(request), expected, msg=request)

    def test_video_beats_viral(self):
        # "viral video" should route to video, the more specific surface.
        intent, _ = route("post a viral video about AI")
        self.assertEqual(intent, "video")


class TestEngagement(unittest.TestCase):
    def test_good_post_passes(self):
        result = engagement.check(GOOD_POST, VIRAL)
        self.assertTrue(result["passed"], msg=result["feedback"])

    def test_question_opener_fails(self):
        text = "Is your AI pilot working?\nMost are not.\n#Leadership #AI #Work"
        self.assertFalse(engagement.check(text, VIRAL)["passed"])

    def test_emoji_fails_when_disallowed(self):
        text = GOOD_POST.replace("workflow.", "workflow." + EMOJI)
        self.assertFalse(engagement.check(text, VIRAL)["passed"])


class TestGuardrailRules(unittest.TestCase):
    def test_clean_passes(self):
        text = "We work the problem until your team can run it without us."
        self.assertTrue(guardrails.run_guardrails(text)["clean"])

    def test_hype_words_banned(self):
        # Metis bans hustle vocabulary.
        result = guardrails.run_guardrails("Let's leverage synergy to unlock growth.")
        self.assertFalse(result["clean"])
        self.assertTrue(result["banned_phrases"])

    def test_antithesis_detected(self):
        self.assertTrue(
            guardrails.find_antithesis("It isn't about tools, it's about behavior.")
        )


class TestVideoCurator(unittest.TestCase):
    def test_select_top_picks_highest_score(self):
        videos = [
            {"title": "A", "relevance_score": 3},
            {"title": "B", "relevance_score": 9},
            {"title": "C", "relevance_score": 6},
        ]
        self.assertEqual(select_top(videos)["title"], "B")

    def test_select_top_empty(self):
        self.assertIsNone(select_top([]))

    def test_credit_line_and_post_assembly(self):
        video = {"title": "Demo", "creator": "@ai_ecosystem",
                 "source_url": "https://x.com/ai_ecosystem/status/1"}
        credit = _credit_line(video)
        self.assertIn("@ai_ecosystem", credit)
        self.assertIn("https://x.com/ai_ecosystem/status/1", credit)
        post = build_post(video, "Sharp take on the clip.")
        self.assertTrue(post["commentary"].startswith("Sharp take on the clip."))
        self.assertIn(credit, post["commentary"])


if __name__ == "__main__":
    unittest.main()
