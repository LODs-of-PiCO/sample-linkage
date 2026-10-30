# Linking baptisms to marriages

Analysis of 30 October 2026. Set-up: burgerLinker v0.8.2 with [models/elo-dtb-marriages.yaml](../models/elo-dtb-marriages.yaml) and burgerLinker's own `LINKS.yaml`, run on the elo-dtb test sample (`8166a65`, 395 records).

## What is compared

`between_b_m` takes the **parents** of a baptised child and compares them with the **bride and groom** of a marriage record:

- father ↔ groom, mother ↔ bride;
- for both, the given name and the surname must match (same Levenshtein limits and first-letter block as in [analysis-kloeck-siblings.md](analysis-kloeck-siblings.md#how-burgerlinker-compares-parents));
- the baptism must fall within the time window of `LINKS.yaml`, after the marriage.

The child's own name is not compared. Linking a child to its own later marriage is a different function (`within_b_m`).

Baptisms that link to the same marriage are siblings. [scripts/siblings_from_links.py](../scripts/siblings_from_links.py) groups them.

## Data used

| | count | years |
|---|---|---|
| baptism records | 252 | 1604–1811 |
| marriage records (ondertrouw and/or huwelijk, `sourcetypes/549`) | 90 | 1585–1811 |
| marriage records returned by the data model | 88 (102 rows) | |

Notes on the marriage records:

- 14 records have two dates (ondertrouw and huwelijk), which gives two rows each in the query.
- 2 records have text in the date field instead of a date, so the model drops them. This is a data issue to report to elo-dtb:
  - [`933930ce…`](https://www.openarchieven.nl/elo:933930ce-4c52-c9f3-648a-7aace9575c35): "Zie: Schepenhuwelijken Arch.1004 Inv. 204 blad H-229" followed by 1712-05-14;
  - [`2d15dd81…`](https://www.openarchieven.nl/elo:2d15dd81-a69d-29b9-02b4-f81df7ad6606): "Datum trouwen: 1659" with an HTML link to the inventory.
- The parents of bride and groom are not retrieved yet; they are only needed for `between_m_m`.

## Result

| | count |
|---|---|
| links found | 1 |
| sibling groups (2+ baptisms to one marriage) | 0 |
| baptisms linked to 2+ marriages | 0 |

The sample is small and spread over two centuries, so few baptisms have the parents' marriage in it. One link is found:

| | baptism 1792-03-11 ([`293722a3…`](https://www.openarchieven.nl/elo:293722a3-55da-b9aa-7880-6a9dda3929a1)) | ondertrouw 1787-11-09 ([`0faeabf0…`](https://www.openarchieven.nl/elo:0faeabf0-93d2-f6eb-d461-40e7b8de3606)) |
|---|---|---|
| father ↔ groom | Michiel Riebeek | Michiel Riebeek |
| mother ↔ bride | Hester Heus | Hester Heus |
| child | Judik Riebeek (not compared) | — |
| witnesses | Hendrik Heus, Judik Wassaart | Michiel Riebeek, Judik Wallaert |

All four names match exactly (Levenshtein 0); the baptism is 4 years after the ondertrouw. The witnesses are not compared by burgerLinker. Judik Wassaart and Judik Wallaert may be the same person, and the witness Michiel Riebeek is probably the groom's father; both would need a witness-level comparison that burgerLinker does not have.

## The Kloeck baptisms and the 1649 ondertrouw

The known Kloeck siblings (see [analysis-kloeck-siblings.md](analysis-kloeck-siblings.md)) have their parents' ondertrouw in the sample ([`fe0bf28c…`](https://www.openarchieven.nl/elo:fe0bf28c-e481-bdaa-48aa-fd2619b70c35), 1649-11-19), but neither baptism links to it.

| | 1649 ondertrouw | 1651 Janneken | 1655 Francois |
|---|---|---|---|
| groom / father, given name | Frans | Frans | Francois |
| groom / father, surname | **Clouck** (patronym Pietersz) | **Kloeck** (patronym Pietersz) | **Pietersz** |
| bride / mother, given name | Jaecquemyntgen | Jacomijntie | Jacomijntje |
| bride / mother, surname | **de Graef** (patronym Isaac) | **de Graefs** | **Isaax** |

Bold: the name the data model passes to burgerLinker as surname.

| comparison with 1649 | names | differences | allowed | result |
|---|---|---|---|---|
| 1651 father, given name | Frans ↔ Frans | 0 | 1 | match |
| 1651 father, surname | Kloeck ↔ Clouck | 2 | 2 | **blocked** (K ≠ C) |
| 1651 mother, given name | Jacomijntie ↔ Jaecquemyntgen | 8 | 3 | no match |
| 1651 mother, surname | de_Graefs ↔ de_Graef | 1 | 3 | match |
| 1655 father, given name | Francois ↔ Frans | 3 | 1–2 | no match |
| 1655 father, surname | Pietersz ↔ Clouck | 8 | 2 | no match |
| 1655 mother, given name | Jacomijntje ↔ Jaecquemyntgen | 8 | 3 | no match |
| 1655 mother, surname | Isaax ↔ de_Graef | 7 | 1 | no match |

What each fix would do:

1. **Pass both surname and patronym** (step 3). For 1655 the father's Pietersz then matches the groom's patronym and Isaax matches Isaac (1 difference). For 1651 it changes nothing.
2. **`--ignore-block`**. Lets Kloeck ↔ Clouck through for 1651 (2 differences, allowed).
3. **Standardise given names** (step 4). Needed for Jacomijntie/Jacomijntje ↔ Jaecquemyntgen in both baptisms and Francois ↔ Frans in 1655. Without it neither baptism can link, whatever else is done.

With all three, both baptisms would link to the 1649 ondertrouw and form a sibling group.
