# Why the Kloeck siblings are not linked

Analysis of 30 October 2026. Set-up: burgerLinker v0.8.2 with [models/elo-dtb-siblings.yaml](../models/elo-dtb-siblings.yaml) and [rules/siblings.yaml](../rules/siblings.yaml), run on the elo-dtb test sample.

## The expected match

The elo-dtb test sample ([sample/README.md](https://github.com/ivozandhuis/elo-dtb/blob/main/sample/README.md)) contains two baptisms of children of Frans Pietersz Kloeck and Jacomijntje Isaaks de Graaf:

| Baptism | Record | Child |
|---|---|---|
| 1651-12-24 | [`1c1c97e7…`](https://www.openarchieven.nl/elo:1c1c97e7-f9a7-40ea-c147-226c6817c9a1) | Janneken Kloeck |
| 1655-09-28 | [`7adcc50e…`](https://www.openarchieven.nl/elo:7adcc50e-082b-04b4-8a91-17ea03827bee) | Francois (Frans Fransz Cloek) |

Hand-made reconstruction: [Jacomijntje Isaaks](https://www.genealogieonline.nl/kwartierstaten-zandhuis-van-der-sloot-borgman-meijer/I1242.php).

## Data used

The local copy of elo-dtb was behind [ivozandhuis/elo-dtb](https://github.com/ivozandhuis/elo-dtb). The 1655 baptism was only added in the extended test sample (commit `4aab3d7`). After updating to `8166a65` the sample has 395 records.

## Result

| | count |
|---|---|
| baptisms with two parents | 232 |
| indexed (both parents have a given name and a surname or patronym) | 227 |
| links found | 227 |
| links that pass the time rule (±25 years) | 225 |
| links between different baptisms | **0** |

All 225 links are baptisms matching themselves. Both Kloeck baptisms are among them, so they are loaded and indexed, but they do not match each other. The 2 rejected links are baptisms whose date has only a year and month (`xsd:gYearMonth`), which burgerLinker cannot read.

## How burgerLinker compares parents

From the burgerLinker source (`Between.java`, `Index.java`, `Person.java`):

- Both parents must match, and for each parent both the given name and the surname must match.
- A name matches if the number of letter differences (Levenshtein distance) is within a limit that depends on the length of the name. With `--max-lev 4`:

  | name length | letters allowed to differ |
  |---|---|
  | 1 | 0 |
  | 2–5 | 1 |
  | 6–8 | 2 |
  | 9–11 | 3 |
  | 12+ | 4 |

- Names are compared case-sensitively.
- Spaces in names become `_`, so "de Graefs" is compared as `de_Graefs`.
- The surname must start with the same letter in both records, unless `--ignore-block` is used.

## The names in both records

| | 1651 Janneken | 1655 Francois |
|---|---|---|
| father, given name | Frans | Francois |
| father, surname | **Kloeck** | — |
| father, patronym | Pietersz | **Pietersz** |
| mother, given name | Jacomijntie | Jacomijntje |
| mother, surname | **de Graefs** | — |
| mother, patronym | — | **Isaax** |

Bold: the name our data model passes to burgerLinker as surname (the family name, or the patronym if there is no family name).

## Pair by pair

| comparison | names | differences | allowed | result |
|---|---|---|---|---|
| father, given name | Frans ↔ Francois | 3 | 1 | no match |
| father, surname | Kloeck ↔ Pietersz | 7 | 2 | no match |
| mother, given name | Jacomijntie ↔ Jacomijntje | 1 | 3 | match |
| mother, surname | de_Graefs ↔ Isaax | 8 | 3 | no match |

Three of the four comparisons fail, each for its own reason:

1. **Father's surname.** Both records have the patronym Pietersz (0 differences), but the data model only uses the patronym when there is no family name. In 1651 there is one (Kloeck), so Pietersz is not used. Passing both name forms would make this pair match.
2. **Father's given name.** Frans and Francois are the same name in Dutch and French spelling. Letter tolerance cannot catch this; it needs given-name standardisation (for example the Bloothooft list in elo-dtb's `lookup-tables/`).
3. **Mother's surname.** The two records have no name form in common: 1651 has only the surname (de Graefs), 1655 only the patronym (Isaax). Passing both forms does not help. Only a record that has both forms can connect them.

## The marriage record as a bridge

The 1649 ondertrouw ([`fe0bf28c…`](https://www.openarchieven.nl/elo:fe0bf28c-e481-bdaa-48aa-fd2619b70c35)) has the mother as "Jaecquemyntgen Isaac de Graef", with both forms. Her surname would match from both baptisms:

| comparison | differences | allowed | result |
|---|---|---|---|
| 1651 `de_Graefs` ↔ 1649 `de_Graef` | 1 | 3 | match |
| 1655 `Isaax` ↔ 1649 `Isaac` | 1 | 1 | match |
| 1651 `Jacomijntie` ↔ 1649 `Jaecquemyntgen` | 8 | 3 | no match |

Her given name fails here too, so given-name standardisation is needed whichever route is taken.

## Casper Stedink

No baptism in the sample has a Casper or Jasper Steven/Steedink as a parent. According to the sample README, Casper Steven married the widow Jaecquemijntgen Isaacx in 1656 ([`133850a5…`](https://www.openarchieven.nl/elo:133850a5-15e2-e703-9e6e-3d538d60a606)) and was Frans Fransz's stepfather. A stepchild or half-sibling cannot be found by matching couples. The 1678 and 1687 marriages of Frans Fransz listed in the sample README are not in the sample directory.

## Possible fixes

1. **Pass both surname and patronym** for each parent to burgerLinker. Fixes the father's surname.
2. **Standardise given names** (Frans/Francois, Jacomijntje/Jaecquemyntgen). Needed in every route.
3. **Link baptisms to marriage records** (`between_b_m` against the ondertrouw/huwelijk records). The only option here that also connects the mother's two name forms.
