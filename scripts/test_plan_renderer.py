import unittest
from plan_renderer import render_plan_html


class PlanRendererTests(unittest.TestCase):
    def render(self, md):
        return render_plan_html(md, "implementation_plans/x/plan.md")

    def test_bullet_header_renders_as_meta_chips(self):
        html = self.render("# T\n\n- Plan version: v2\n- Updated: 2026-09-26\n- Status: in review\n\n## Outcome\n\nx\n")
        for key in ("Plan version", "Updated", "Status"):
            self.assertIn(f"<b>{key}</b>", html)

    def test_leading_list_that_is_not_key_value_stays_visible(self):
        html = self.render("# T\n\n- first point\n- second point\n\n## Outcome\n\nx\n")
        self.assertIn("<li>first point</li>", html)
        self.assertIn("<li>second point</li>", html)

    def test_table_above_first_section_stays_visible(self):
        html = self.render("# T\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n## Outcome\n\nx\n")
        self.assertIn("<table>", html)

    def test_milestone_headings_render_as_cards(self):
        html = self.render("# T\n\n## Milestones\n\n### Milestone 1: Journey works (done)\n\ny\n\n## Milestone B: Next\n\nz\n\n### M3 Short form\n\nw\n")
        self.assertEqual(html.count('class="milestone"'), 3)
        self.assertIn('class="done"', html)

    def test_owner_choice_sections_render_as_decision_cards(self):
        html = self.render("# T\n\n## Open owner choices\n\n1. D1: pick A or B. Recommendation: A\n")
        self.assertIn('class="decision"', html)
        self.assertIn('class="rec"', html)


if __name__ == "__main__":
    unittest.main()
