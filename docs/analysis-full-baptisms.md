# Siblings in the full ELO baptism set

Analysis of 30–31 October 2026. Set-up: burgerLinker v0.8.2, function `between_b_m` with the sibling data models below and [rules/siblings.yaml](../rules/siblings.yaml). Tested on the baptisms of 1700–1704; the full runs are still to be done.

## From the dump to the baptism set

The source is a full PiCo dump of Erfgoed Leiden en Omstreken (`elo-pico.nt.gz`, 1.5 GB compressed, 125 million triples, about 2.9 million records). It is the data behind the ELO endpoint <https://qlever.coret.org/elo>, but the records in the dump have **no record type**: the endpoint's baptism type `…/ThesaurusHistorischePersoonsgegevens/548` is not in it.

The endpoint was not used for linking. burgerLinker sends one query per candidate link, which on the endpoint would mean hundreds of thousands of requests (about 0.2 s each), and a single large export is cut off by the server after about 3 minutes.

Two scripts make the baptism set (all output in `data/`, which is not in git):

| step | script | result | time |
|---|---|---|---|
| 1 | [scripts/extract_child_records.sh](../scripts/extract_child_records.sh) | every record with a child (role 575) and only the triples needed: 746,491 records, 28.4 million triples | 7 min |
| 2 | [scripts/select_baptisms.sh](../scripts/select_baptisms.sh) | the baptisms before 1811, with only the child and its parents: 395,690 baptisms, 8.8 million triples | 1 min |

### Which records are baptisms

Role 575 is also used for the child in civil birth registers (Burgerlijke Stand), so a child alone does not make a baptism. A record is taken as a baptism when one of its descriptions contains "Doopdatum". This marker is per record, so it also finds the baptism books kept in municipal archives (Zoeterwoude, Leiderdorp, Rijnsburg …), which a selection on collection name would miss.

| records with a child (744,759 with a collection name in `sdo:name`) | count |
|---|---|
| "Doopdatum", dated before 1811 | 398,653 |
| "Doopdatum", dated 1811 or later | 1,792 |
| no "Doopdatum", dated before 1811 | 207 |
| no "Doopdatum", dated 1811 or later | 6,318 |
| no date at all (nearly all civil registers) | 337,789 |

### Cut-off at 1811

Civil registration started in 1811 and the church registers mostly stop then, so the set is limited to baptisms **before 1811**. A side effect: a child baptised shortly before 1811 cannot be linked to a sibling born after it.

### Dates

Of the 398,653 baptisms before 1811, 2,963 are dropped because burgerLinker cannot read their date: 1,247 have only a year, 1,700 only a year and month, and 16 a broken date typed as `xsd:date` ("1700-NaN-07"). That leaves **395,690 baptisms**.

`select_baptisms.sh` gives each baptism the endpoint's baptism type, so the same data model works on both, and adds `rdf:type` for records and persons: burgerLinker's dataset summary fails on a store without any `rdf:type` ("count is negative").

## How we match

The sibling method from [the sample](analysis-kloeck-siblings.md): every baptism's parent couple is also offered to burgerLinker as a "marriage", and `between_b_m` links the parents of one baptism to the parents of another. For each pair of baptisms:

1. Father is compared with father, mother with mother. **Both** parents must match.
2. For each parent, the **given name and the "surname"** must both match.
3. A name matches when the number of letter differences (Levenshtein distance) is within a limit set by the length of the name being searched for: 1 letter 0, 2–5 letters 1, 6–8 letters 2, 9–11 letters 3, 12+ letters 4. Case counts; spaces and hyphens become `_`. A multi-part given name is also tried part by part ("Jan Hendrick" as "Jan", "Hendrick" and "Jan Hendrick").
4. The surname must start with the **same letter** in both records.
5. The two baptisms may be at most **25 years** apart.
6. A baptism also links to itself; those links are dropped. Baptisms that link are sibling candidates.

burgerLinker does not standardise spelling: "ck" and "k" are different letters, and "Hendrick" ↔ "Hendrik" only matches because one letter of difference is allowed. Short names have little room (Claes ↔ Klaas: 2 differences, 1 allowed), and variants at the first letter of a surname never link (Kloeck ↔ Clouck, Cornelis ↔ Kornelis).

### Two runs for the surname

| run | "surname" | data model |
|---|---|---|
| family name | `sdo:familyName` as written, including the prefix ("van den Bosch") | [models/elo-baptisms-familyname.yaml](../models/elo-baptisms-familyname.yaml) |
| patronym | `pnv:patronym` only | [models/elo-baptisms-patronym.yaml](../models/elo-baptisms-patronym.yaml) |

There is no fallback between them: a parent without that name form is left out of that run.

## Standardised given names

[scripts/standardise_given_names.py](../scripts/standardise_given_names.py) adds a standardised given name to every person (`slk:standardGivenName`), next to the original, from Bloothooft's given-name list (elo-dtb `lookup-tables/bloothooft-given-names.nt.gz`):

1. "N.n." (name unknown) gets no standardised name, so that parent is not matched.
2. `*` is removed; brackets inside a word are dropped ("Cath(arina)" → "Catharina"); a name in brackets after a space becomes an extra given name ("Grietje (Margrietgen)").
3. The name is split on spaces and hyphens, and each part is replaced by its standard form (`gn_standard`), in the original order. When a name occurs more than once in the list, the most used entry (`gn_tokens_firstname`) decides. Parts that are not in the list, or have no standard, are kept, in lower case.

The list holds single names only (none of its 189,705 entries contains a space), which is why each part is looked up separately. Of the 1,137,599 given names in the baptism set, 6,875 are "N.n."; of the name parts, 96.6% have a standard form.

Examples:

| names | standard |
|---|---|
| Jan, Johannes, Joannes, Hans | johannes |
| Hendrick, Hendrik, Heindrick | heimrijk |
| Claes, Klaas, Nicolaas | nicolaas |
| Frans, Francois | franciscus |
| Anna, Antje, Anneke | anne |
| Neeltje, Cornelia | cornelis |
| Jacomijntje, Jacomijntie | jacob |
| Maritgen, Margrietgen, Jaecquemyntgen | not in the list |

The standard forms are root forms, often the male form ("Neeltje" → "cornelis"); since a mother is only compared with a mother this does no harm. Several 17th-century spellings ending in "-gen" are missing from the list.

The data models with standardised given names for the parents are [models/elo-baptisms-familyname-std.yaml](../models/elo-baptisms-familyname-std.yaml) and [models/elo-baptisms-patronym-std.yaml](../models/elo-baptisms-patronym-std.yaml).

## Test on 1700–1704

12,913 baptisms.

| run | indexed | sibling pairs | gained | lost | sibling groups | time |
|---|---|---|---|---|---|---|
| family name | 8,044 | 2,260 | | | 1,373 | 22 s |
| family name, standardised | 8,043 | 2,631 | 433 | 62 | 1,538 | 22 s |
| patronym | 2,620 | 744 | | | 460 | 7 s |
| patronym, standardised | 2,620 | 877 | 175 | 42 | 502 | 8 s |

Only 120 pairs are found by both the family-name and the patronym run (without standardisation): the two runs mostly reach different couples.

Spot checks of the family-name run show the letter tolerance at work: "van Roojen" ↔ "van Roijen", "Lauwerens" ↔ "Laurens", "Engeltje Torenaer" ↔ "Engeltie Torenar". Twins baptised on the same day and two children of the same name a year apart (an earlier child that died) also show up as siblings, as they should.

### Gained by standardisation

- Henric ↔ Heindrik de Wit(te) (both "heimrijk")
- Ysaack ↔ Isak van Drongen ("izaak")
- Hendrick ↔ Heijndrik van Dijk/Dick, with Jacomijntje ↔ Jacomina ("heimrijk", "jacob")
- Roeloff ↔ Roelof Jansse, with Antje ↔ Annetie Dircks ("rodwolf", "anne")

### Lost by standardisation

A pair is lost when one spelling is in the list and the other is not, or when two spellings get different standards; the names then end up further apart than before:

- Maertje → "maria", but Maertie is not in the list and stays "maertie" (3 differences)
- Magdaleentje → "magdalena", but Magdaleentjen stays as written
- Reijnder → "reinhard", but Reijniers → "reingeer"
- Barent → "bernhard", but Barentt stays as written

### Risk

In the patronym run, common combinations such as "Pieter Jansz & Marij Jans" link more easily after standardisation. Some of these may be different couples with the same names; precision still has to be checked on a sample.

## Union of the runs

Decision: keep the plain and the standardised runs and use the **union** of their sibling pairs, so that the pairs lost by standardisation are kept from the plain run. [scripts/sibling_groups.py](../scripts/sibling_groups.py) combines any number of runs, records for every pair which runs found it, and forms sibling groups (if A–B and B–C are pairs, A, B and C are one group).

On 1700–1704, all four runs together:

| found by | pairs |
|---|---|
| family name, plain and standardised | 2,084 |
| patronym, plain and standardised | 588 |
| family name, standardised only | 424 |
| patronym, standardised only | 166 |
| all four runs | 114 |
| family name, plain only | 56 |
| patronym, plain only | 36 |
| other combinations | 15 |
| **union** | **3,483** |

That gives 1,991 sibling groups with 4,694 baptisms (sizes 2: 1,412; 3: 461; 4: 107; 5: 8; 6: 2; 7: 1).

### Groups that join different couples

Because a group is everything connected by pairs, one wrong pair can join two families. The largest groups show that this happens with common patronyms:

- The group of 7 is "Pieter Jansz & Marij Jans" in several forms, with family names Nap/Stult, Schuijn and van den Berg in some records: at least three different couples, linked through the records that have no family name.
- A group of 6, "Jan Pietersz & Marijtie Cornelis", has baptisms on 1702-03-30 and 1702-06-04, two months apart, which one mother cannot have.
- A group of 6, "Willem Anselijn & Susanna van Heesen", is plausible. It has two pairs of records with the same date: on 1700-12-01 the twins Daniel and Willem, and on 1701-12-21 two records of the same child Maria (once "Anselijn", once "Anseleijn"), one baptism registered twice.

Possible checks before the groups are used:

1. Do not link two parents who both have a family name that differs, even when their patronyms match.
2. Reject pairs, or split groups, with two baptisms less than about 9 months apart, unless they are on the same day (twins or a double registration).
3. Mark records with the same date, the same child's name and the same parents as possible double registrations (twins have the same date but different names).
