"""Static contract tests for the AtroZ dashboard HTML."""

import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT / "src" / "saaaaaa" / "api" / "static" / "index.html"


class IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []

    def handle_starttag(self, tag, attrs):  # type: ignore[override]
        for key, value in attrs:
            if key == "id" and value:
                self.ids.append(value)


def _load_html() -> str:
    assert HTML_PATH.exists(), "Dashboard HTML should exist"
    return HTML_PATH.read_text(encoding="utf-8")


def test_dashboard_surfaces_expert_sections():
    parser = IdCollector()
    parser.feed(_load_html())

    expected_ids = {
        "designBlueprints",
        "eliteGallery",
        "metricStack",
        "latencySpark",
        "managementLayer",
        "stealthEntry",
        "conceptTribunal",
        "tribunalVoices",
        "integralConcept",
        "conceptNarrative",
        "tribunalTags",
        "conceptText",
    }
    missing = expected_ids.difference(parser.ids)
    assert not missing, f"Missing IDs in dashboard: {missing}"


def test_concept_tribunal_declares_integral_view():
    content = _load_html()

    for name in ["Doris Salcedo", "O. de Sagazan", "Adorno"]:
        assert name in content, f"Tribunal voice missing: {name}"

    assert "Concepto integral del dashboard" in content, "Integral concept statement should be present"


def test_reservoir_and_blueprints_have_depth():
    content = _load_html()
    reservoir_block = re.search(r"const graphReservoir = \[(.*?)\];", content, flags=re.S)
    assert reservoir_block, "Graph reservoir should be declared"
    reservoir_names = re.findall(r"name:\s*'", reservoir_block.group(1))
    assert len(reservoir_names) >= 24, "Reservoir should expose dozens of graph options"

    blueprint_block = re.search(r"const designBlueprints = \[(.*?)\];", content, flags=re.S)
    assert blueprint_block, "Design blueprints must be present"
    blueprint_items = re.findall(r"title:\s*'", blueprint_block.group(1))
    assert len(blueprint_items) >= 5, "Need multiple expert-level blueprints"


def test_latency_history_seeded_for_metrics():
    content = _load_html()
    history_seed = re.search(r"latency: Array.from\(\{ length: (\d+) \}", content)
    assert history_seed, "Telemetry history seed must exist"
    assert int(history_seed.group(1)) >= 32, "Telemetry history should start with a robust baseline"

