import pytest

from pslecompiler.parse_pdf import Section
from pslecompiler.sources import SourceDoc
from pslecompiler.structure import build_spine
from pslecompiler.extract import apply_extractions
from pslecompiler.extract.schema import Extraction, Misconception
from pslecompiler.model import LEARNING_OUTCOME


SCIENCE_SRC = SourceDoc(
    filename="science-primary-2023.pdf", subject="Science", version="2023",
    effective_year=2023, level="Standard", title="Test Science 2023",
    url="https://example.test/science", mapper="science_2023",
)


@pytest.fixture
def science_sections():
    return [
        Section(level=1, title="Cycles", text="", page=5),
        Section(level=2, title="Matter (P3)", text="", page=6),
        Section(
            level=99, title="", page=6,
            text=("• Pupils should be able to state that matter has mass and "
                  "occupies space.\n"
                  "• Pupils should be able to compare the three states of "
                  "matter: solid, liquid and gas."),
        ),
        Section(level=1, title="Systems", text="", page=20),
        Section(level=2, title="Plant System (P5)", text="", page=21),
        Section(
            level=99, title="", page=21,
            text=("• Pupils should be able to identify the parts of the plant "
                  "transport system."),
        ),
    ]


@pytest.fixture
def science_kg(science_sections):
    kg = build_spine(science_sections, SCIENCE_SRC)
    # attach one extraction to the first learning outcome
    los = sorted(kg.nodes_with_label(LEARNING_OUTCOME),
                 key=lambda n: n.props.get("order", 0))
    lo0 = los[0]
    ext = Extraction(
        lo_uid=lo0.uid,
        concepts=["states of matter", "mass"],
        key_terms=["solid", "liquid", "gas"],
        prerequisites=["matter"],
        related=["volume"],
        commonly_confused_with=[("melting", "dissolving")],
        misconceptions=[Misconception(
            statement="Gases do not have mass.",
            about_concept="states of matter",
            distractor="Gases have no mass because they are invisible.",
        )],
        cognitive_level="comprehension",
        difficulty_band="core",
    )
    apply_extractions(kg, [ext])
    return kg
