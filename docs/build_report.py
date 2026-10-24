"""Stitch docs/REPORT.md from its parts and the generated result tables."""
import os

D = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(D, "..", "results")


def read(p):
    return open(p).read() if os.path.exists(p) else ""


parts = [
    read(os.path.join(D, "REPORT_HEAD.md")).replace("<!-- HEADLINE -->",
                                                    read(os.path.join(D, "REPORT_HEADLINE.md"))),
    read(os.path.join(D, "REPORT_FRAMEWORK.md")),
    read(os.path.join(D, "REPORT_SETUP.md")),
    "## 5. Results on the IBM-127 benchmarks\n\n" + read(os.path.join(D, "REPORT_DISCUSSION.md")) +
    "\n" + read(os.path.join(R, "ibm127", "tables.md")),
    "## 6. Results in the settings of Lee et al. and on structured commuting circuits\n\n" +
    read(os.path.join(D, "REPORT_STRUCTURED.md")) + "\n" + read(os.path.join(R, "structured", "tables.md")),
    read(os.path.join(D, "REPORT_TAIL.md")),
    "## Appendix A. Theory: statements and proofs\n\n" +
    read(os.path.join(D, "THEORY.md")).split("\n", 1)[1],
    "## Appendix B. Related-work study notes\n\n" +
    read(os.path.join(D, "RELATED_WORK.md")).split("\n", 1)[1],
]
with open(os.path.join(D, "REPORT.md"), "w") as fh:
    fh.write("\n\n".join(p.strip() for p in parts if p.strip()) + "\n")
print("wrote docs/REPORT.md")
