# CARISMA-WorkKG: ontology, SHACL shapes and SWING sensitivity analysis [![DOI](https://zenodo.org/badge/1448850855.svg)](https://doi.org/10.5281/zenodo.24024345)

These are the companion files for the paper *CARISMA-WorkKG: A Knowledge Graph Framework for Cybersecurity Capability Assessment and Workforce Investment Prioritization*. We put them together so that anyone can open the ontology, run the validation rules on the case-study data, and reproduce the investment comparison in Section 4.3 without having to ask us for anything.

The package has two independent parts:

```
ontology/   the OWL 2 ontology, the SHACL shapes and the populated case-study graphs
swing/      the SWING investment comparison and its sensitivity analysis (Section 4.3, Figure 4)
```

You need Python 3.10 or newer and four packages, installed with `pip install -r requirements.txt` (rdflib, pySHACL, numpy and matplotlib). Java is not needed for anything in this package.

## 1. The ontology (`ontology/`)

| File | What it is |
|---|---|
| `carisma-workkg-core.ttl` | The ontology itself, in Turtle. This is the version we maintain: 43 classes, 46 object properties, 30 datatype properties and 20 vocabulary individuals, in OWL 2 DL. |
| `carisma-workkg-core.owl` | The same ontology in RDF/XML, which is what Protégé expects. |
| `carisma-workkg-shapes.ttl` | The eleven SHACL shapes (S1–S11) described in Section 3.3 of the paper. |
| `carisma-workkg-scenario-incident-detection.ttl` / `.owl` | The incident-detection capability of the case study, with both the recorded inputs and the computed results (this is what Table 5 and Figure 3 show). It imports the core. |
| `carisma-workkg-scenario-portfolio.ttl` / `.owl` | The six-capability portfolio of Table 7, together with the four investment alternatives of Table 8 and the gaps each of them addresses. It imports the core too. |
| `catalog-v001.xml` | A small helper file so that Protégé finds the core ontology on disk instead of trying to download it. |
| `validate_shacl.py` | A short script that runs the shapes against a scenario file. |

### Looking at the ontology in Protégé

Open `carisma-workkg-scenario-portfolio.owl` (File ▸ Open). The core ontology is pulled in automatically through the catalog file. Then start HermiT from the Reasoner menu. Three things are worth checking: the ontology is consistent; the production SIEM gains `assetRequiresCompetency` links that nobody wrote by hand, because the property chain derives them; and every `RequirementCoverage` individual ends up classified as either `DeficientCoverage` or `UnresolvedCoverage`, because those two are defined classes. These are the inferences the paper refers to in Section 3.2.

### Running the SHACL rules

From inside the `ontology` folder:

```
python validate_shacl.py                                         # checks the portfolio snapshot
python validate_shacl.py carisma-workkg-scenario-incident-detection.ttl
```

Both should print `CONFORMS`. If you prefer the pySHACL command-line tool, the equivalent call is

```
pyshacl -s carisma-workkg-shapes.ttl -e carisma-workkg-core.ttl carisma-workkg-scenario-portfolio.ttl
```

The quickest way to see what the shapes actually do is to break something. Open one of the scenario files, delete the `cw:weight` line of a `CompetencyRequirement` (or set a `cw:coverageStatus` to some value other than Covered, Deficient or Unresolved) and run the script again. The report tells you which shape fired, which node is at fault and why.

### Using your own data

Records follow the classes in Table 1 of the paper, and every property that the scoring needs is enforced by a shape. So if your file passes `validate_shacl.py`, it is complete enough to be scored. The scoring itself, the 40-check validation with HermiT and the sensitivity analysis of the gap priorities live in the full package (`carisma-workkg-v0.3.zip`), which we kept separate because it needs Java.

## 2. The SWING comparison and its sensitivity analysis (`swing/`)

| File | What it is |
|---|---|
| `swing_inputs.json` | Everything the comparison needs: the gap priorities of the five criteria (from Table 7), the swing points derived from them (100 × priority ÷ highest priority), and, for each investment, the expert's range `[low, high]` on each criterion. The scale runs from 0 (the investment changes nothing) to 10 (it closes the capability's gap completely). |
| `swing_analysis.py` | Computes the weights (Eq. 7), the values (Eq. 8) and the scores and ranking (Eq. 9), runs the ±20 % check on the swing points, and writes out the worked example. |
| `swing_figure.py` | Produces Figure 4: panel (a) with the scores and ranking, panel (b) with the lead of the first-ranked investment in the worst and best case for each criterion (Eqs. 10–12). It also prints the score intervals and checks for dominance. |

### Running it

```
cd swing
python swing_analysis.py       # weights, scores, ranking and the weight check
python swing_figure.py         # criterion sensitivity and Figure 4
```

Everything lands in `swing/results/`: `swing_worked_example.md` and `.csv` are Table 8; `swing_sensitivity.csv` is the ±20 % weight check; `swing_criteria_ranges.csv` holds the worst- and best-case lead for each criterion plus the score intervals; and `figures/fig_swing_final.png` and `.pdf` are Figure 4 at 300 dpi.

### Changing the inputs

Edit `swing_inputs.json` and run the two scripts again. If you want to keep several versions side by side, pass a different file with `--inputs other.json`. When you carry the results into the paper, Table 8 comes from `results/swing_worked_example.md` and the text of Section 4.3 from `results/swing_criteria_ranges.csv`. One thing to keep in mind when reading that file: a negative worst-case lead means that the uncertainty in that one criterion is enough on its own to put a different investment in first place.

## Namespaces

The ontology IRI is `https://ict.ihu.gr/carisma-workkg` (version 0.3.0). The scenario data use `.../scenario/incident-detection#`, `.../scenario/portfolio#` and `.../scenario/investments#`.

## License

The ontology, the SHACL shapes, the scenario graphs, the SWING inputs and this documentation are released under the Creative Commons Attribution 4.0 International license (see `LICENSE-CC-BY-4.0`). The Python scripts are under the MIT license (see `LICENSE`). If you build on any of it, we would appreciate a citation of the paper.
