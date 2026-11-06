"""Validate a CARISMA-WorkKG snapshot against the SHACL shapes (no Java needed).

Usage:  python validate_shacl.py [data.ttl]      default: carisma-workkg-scenario-portfolio.ttl
Exit code 0 = conforms, 1 = violations (printed).
"""
import sys
from pathlib import Path
import rdflib, pyshacl

HERE = Path(__file__).resolve().parent
data_file = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "carisma-workkg-scenario-portfolio.ttl"
data = rdflib.Graph()
data.parse(HERE / "carisma-workkg-core.ttl", format="turtle")
data.parse(data_file, format="turtle")
shapes = rdflib.Graph().parse(HERE / "carisma-workkg-shapes.ttl", format="turtle")
ok, _, report = pyshacl.validate(data, shacl_graph=shapes, inference="none", abort_on_first=False)
print(f"{data_file.name}: {'CONFORMS' if ok else 'VIOLATIONS'}")
if not ok:
    print(report)
sys.exit(0 if ok else 1)
