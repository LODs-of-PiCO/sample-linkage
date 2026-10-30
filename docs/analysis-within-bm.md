# Linking baptised children to their own marriage

Analysis of 30 October 2026. Set-up: burgerLinker v0.8.2, function `within_b_m`, burgerLinker's own `LINKS.yaml`, run on the elo-dtb test sample (`8166a65`, 395 records).

## What is compared

`within_b_m` looks for the baptised child as a later bride or groom (from `Within.java`):

- the child's given name and surname must match the bride's or groom's (same Levenshtein limits and first-letter block as in [analysis-kloeck-siblings.md](analysis-kloeck-siblings.md#how-burgerlinker-compares-parents));
- a girl is only compared with brides, a boy only with grooms;
- by default at least one of the child's parents must also match a parent of that bride or groom;
- the marriage must be 14 to 80 years after the baptism.

With `--ignore-relatives` the parents are skipped: only the child's name is compared with the bride's or groom's name.

## Data models

| set-up | data model | child's gender |
|---|---|---|
| `within-bm` | [models/elo-dtb-within-bm.yaml](../models/elo-dtb-within-bm.yaml) | both genders |
| `within-bm-bloothooft` | [models/elo-dtb-within-bm-bloothooft.yaml](../models/elo-dtb-within-bm-bloothooft.yaml) | Bloothooft's given-name list, both genders if the name is not in it |

Both models:

- **Give the child a gender.** burgerLinker skips a child without a gender, and only 1 of the 252 baptised children has one recorded.
  - *Both genders:* every child gets two rows, one as male and one as female, so it is compared with brides and with grooms.
  - *Bloothooft:* [scripts/given_name_gender.py](../scripts/given_name_gender.py) turns elo-dtb's `lookup-tables/bloothooft-given-names.nt.gz` into a name → gender lookup. Some names are listed for both genders with a usage count (Frans: 97,496 male, 40 female); the most used gender is kept. 223 of the 254 child observations get a gender this way. The 31 that do not are mostly double names (Anna Maria, Johanna Maria, Willem Frederik), because only the full given name is looked up.
- **Use the patronym as surname** when the child has no family name, as for the parents. 206 children have a family name or patronym; the other 46 cannot be linked.
- **Retrieve the parents of bride and groom.** In the ELO marriage records these are witnesses (role 573) linked to the bride or groom with `sdo:parent`. Of the 102 marriage rows, 22 have a parent of the bride and 17 a parent of the groom; mostly only the mother of the bride or the father of the groom.

## Result

| child's gender | strict (a parent must match too) | names only (`--ignore-relatives`) |
|---|---|---|
| both genders | 0 | 4 |
| Bloothooft | 0 | 4 (the same file) |

### Strict

No links. With only 39 brides and grooms with a known parent, there is little to match. burgerLinker finds no child that matches one of them on both its own name and a parent's name.

### Names only

| baptism | child | marriage | bride / groom | years | verdict |
|---|---|---|---|---|---|
| 1683-01-03 [`3e75aab2…`](https://www.openarchieven.nl/elo:3e75aab2-57ba-94df-c41e-06efd335e2d0) | Geertruijdt Elisabeth van der Lith | 1757-04-22 [`08b51c36…`](https://www.openarchieven.nl/elo:08b51c36-4214-202d-5b73-7a68e910fc35) | Geertruij van der Burg | 74 | wrong |
| 1695-03-20 [`58ffa423…`](https://www.openarchieven.nl/elo:58ffa423-952b-9840-534e-9691fbfba9a1) | Maria van der Lelij | 1726-05-17 [`4124a4ea…`](https://www.openarchieven.nl/elo:4124a4ea-e454-93cd-6ce2-b59661b2b606) | Maria van der Velden | 31 | wrong |
| 1759-07-29 [`9d0db054…`](https://www.openarchieven.nl/elo:9d0db054-4c32-1989-511c-baf87fe1f2d0) | Anna van Weeren | 1774-11-21 [`fa81e44a…`](https://www.openarchieven.nl/elo:fa81e44a-93b9-b51a-3ba5-af36bff4a606) | Anna van Veen | 15 | wrong |
| 1651-02-28 [`bebce6d5…`](https://www.openarchieven.nl/elo:bebce6d5-eebb-7424-7f95-3b6d26e042d0) | Jacob de Swijger | 1722-02-14 [`844c4884…`](https://www.openarchieven.nl/elo:844c4884-e484-a959-fc72-70f8c2d3e606) | Jacob de Swijger | 70 | doubtful |

The three wrong links have clearly different surnames, but the allowed number of differences depends on the length of the whole surname, including the prefix:

| names | length | differences | allowed |
|---|---|---|---|
| van_der_Lith ↔ van_der_Burg | 12 | 4 | 4 |
| van_der_Lelij ↔ van_der_Velden | 13 | 4 | 4 |
| van_Weeren ↔ van_Veen | 10 | 3 | 3 |

In the first link only one of the child's two given names is matched: Geertruijdt ↔ Geertruij (2 differences).

Jacob de Swijger matches exactly, but he would have been 70 at this ondertrouw, so the groom is more likely a grandson with the same name. The 1722 record has no parents to check this.

### Why the gender lookup changed nothing

With both genders, a child is also compared with the brides or grooms of the wrong sex. Those comparisons almost never pass on the given name, so they added no links. The lookup halves the rows (and stops a Maria being compared with grooms), which will matter more on a large data set than on this sample.

## Conclusions

1. **Names-only matching is not reliable here.** Long surnames with prefixes (van der, van den) get a large Levenshtein allowance. Removing the prefix before comparing, or using `--fixed-lev` with a lower `--max-lev`, would make this stricter.
2. **The parent check is limited by the data.** Most ELO marriage records do not name the parents of bride and groom.
3. **The sample is small for this question.** A child's own marriage falls 14 to 80 years after the baptism, and the 395 records spread over two centuries hold few such pairs.
