# sample-linkage

Finding siblings in the Leiden baptism records (ELO DTB, 17th/18th century) with [burgerLinker](https://github.com/CLARIAH/burgerLinker). The data comes from [elo-dtb](https://github.com/rlzijdeman/elo-dtb), in the [PiCo](https://personsincontext.org/model) model.

## Idea

burgerLinker has no step that compares the parents of one baptism with the parents of another. It does have `between_b_m`, which links the parents of a newborn to the bride and groom of a marriage. Because burgerLinker reads the data through SPARQL queries that we can supply ourselves, our data model ([models/elo-dtb-siblings.yaml](models/elo-dtb-siblings.yaml)) tells it that:

- **BIRTHS** are the baptised children, each with father and mother;
- **MARRIAGES** are the parent couples of those same baptisms (mother = bride, father = groom).

`between_b_m` then links the parents of baptism A to the parents of baptism B. Two baptisms that link are sibling candidates.

Choices made in the data model and rules:

- **Patronym as surname.** Many parents have only a patronym (`pnv:patronym`) and no `sdo:familyName`. The patronym is used as the surname when there is no family name; otherwise burgerLinker would skip these parents.
- **Time window.** [rules/siblings.yaml](rules/siblings.yaml) is burgerLinker's `LINKS.yaml` with one change: two baptisms may be at most 25 years apart, in either order.
- **Both parents needed.** Baptisms with only one parent recorded are not linked.

## Set-up

Needs Java 17 or newer (`openjdk-21-jre-headless` on Debian) and Python 3 with `rdflib`.

Download [burgerLinker v0.8.2](https://github.com/CLARIAH/burgerLinker/releases/tag/v0.8.2) and unzip it into `bin/`:

```bash
mkdir -p bin && cd bin && gh release download v0.8.2 -R CLARIAH/burgerLinker && unzip burgerlinker-v0.8.2.zip -d burgerlinker-v0.8.2
```

## Running

burgerLinker reads files, not directories, so first merge the elo-dtb Turtle files into one file:

```bash
python3 scripts/merge_ttl.py ../elo-dtb/sample data/elo-dtb-sample.nt
```

For the elo-dtb sample there are four set-ups:

| set-up | function | links | data model | rules |
|---|---|---|---|---|
| `siblings` | `between_b_m` | parents of a baptism → parents of another baptism | [models/elo-dtb-siblings.yaml](models/elo-dtb-siblings.yaml) | [rules/siblings.yaml](rules/siblings.yaml) |
| `marriages` | `between_b_m` | parents of a baptism → bride and groom of a marriage | [models/elo-dtb-marriages.yaml](models/elo-dtb-marriages.yaml) | burgerLinker's `LINKS.yaml` |
| `within-bm` | `within_b_m` | baptised child → bride or groom of a marriage; the child gets both genders | [models/elo-dtb-within-bm.yaml](models/elo-dtb-within-bm.yaml) | burgerLinker's `LINKS.yaml` |
| `within-bm-bloothooft` | `within_b_m` | same, with the child's gender from Bloothooft's given-name list | [models/elo-dtb-within-bm-bloothooft.yaml](models/elo-dtb-within-bm-bloothooft.yaml) | burgerLinker's `LINKS.yaml` |

```bash
scripts/run.sh siblings data/elo-dtb-sample.nt work/sample
scripts/run.sh marriages data/elo-dtb-sample.nt work/marriages
scripts/run.sh within-bm data/elo-dtb-sample.nt work/within-bm
```

`within-bm-bloothooft` needs a name → gender lookup in the input. Build it once from elo-dtb's lookup table (takes about half a minute) and add it to the data:

```bash
python3 scripts/given_name_gender.py ../elo-dtb/lookup-tables/bloothooft-given-names.nt.gz data/given-name-gender.nt
cat data/elo-dtb-sample.nt data/given-name-gender.nt > data/elo-dtb-sample-with-gender.nt
scripts/run.sh within-bm-bloothooft data/elo-dtb-sample-with-gender.nt work/within-bm-bloothooft
```

Extra burgerLinker options go at the end, for example `--ignore-relatives` to compare only the child with the bride or groom, without their parents. The results then go to a directory ending in `-singleInd`.

The links are in `<workdir>/between_b-m-maxLev-4/results/BETWEEN_B-M-maxLev-4.csv` (`within_b-m-…` for the `within-bm` set-ups). In the `siblings` set-up every baptism also links to itself (`certificate_A` = `certificate_B`); those rows can be ignored. A workdir keeps its RDF store; delete the workdir to load new data.

In the `marriages` set-up, baptisms that link to the same marriage are siblings. To group them:

```bash
python3 scripts/siblings_from_links.py work/marriages/between_b-m-maxLev-4/results/BETWEEN_B-M-maxLev-4.csv work/marriages/siblings.csv
```

It also lists baptisms that link to more than one marriage.

## Full ELO baptism set

The siblings of all ELO baptisms before 1811 come from a full PiCo dump of Erfgoed Leiden en Omstreken (`data/elo-pico.nt.gz`, not in git). Make the baptism set (about 8 minutes), add the standardised given names (Bloothooft) and run four set-ups: family name or patronym as surname, each with the given names as written and standardised:

```bash
scripts/extract_child_records.sh data/elo-pico.nt.gz data/elo-child-records.nt
scripts/select_baptisms.sh data/elo-child-records.nt data/elo-baptisms-before-1811.nt
python3 scripts/standardise_given_names.py ../elo-dtb/lookup-tables/bloothooft-given-names.nt.gz data/elo-baptisms-before-1811.nt data/elo-baptisms-before-1811-std.nt
scripts/run.sh siblings-familyname data/elo-baptisms-before-1811-std.nt work/familyname
scripts/run.sh siblings-familyname-std data/elo-baptisms-before-1811-std.nt work/familyname-std
scripts/run.sh siblings-patronym data/elo-baptisms-before-1811-std.nt work/patronym
scripts/run.sh siblings-patronym-std data/elo-baptisms-before-1811-std.nt work/patronym-std
```

| set-up | surname | given names | data model |
|---|---|---|---|
| `siblings-familyname` | `sdo:familyName` | as written | [models/elo-baptisms-familyname.yaml](models/elo-baptisms-familyname.yaml) |
| `siblings-familyname-std` | `sdo:familyName` | standardised | [models/elo-baptisms-familyname-std.yaml](models/elo-baptisms-familyname-std.yaml) |
| `siblings-patronym` | `pnv:patronym` | as written | [models/elo-baptisms-patronym.yaml](models/elo-baptisms-patronym.yaml) |
| `siblings-patronym-std` | `pnv:patronym` | standardised | [models/elo-baptisms-patronym-std.yaml](models/elo-baptisms-patronym-std.yaml) |

The sibling pairs and groups are the union of the four runs:

```bash
R=between_b-m-maxLev-4/results/BETWEEN_B-M-maxLev-4.csv
python3 scripts/sibling_groups.py work/siblings familyname=work/familyname/$R familyname-std=work/familyname-std/$R patronym=work/patronym/$R patronym-std=work/patronym-std/$R
```

This writes `work/siblings-pairs.csv` (with the runs that found each pair) and `work/siblings-groups.csv`. How the baptisms are selected, how the names are matched and what the test on 1700–1704 showed is in [docs/analysis-full-baptisms.md](docs/analysis-full-baptisms.md).

Common patronyms ("Jan & Maria") join different couples into one group. `--family-name-check <baptisms.nt>` drops a pair found only by the patronym runs when the fathers, or the mothers, both have a family name and those differ (compared without prefix, with burgerLinker's tolerance):

```bash
python3 scripts/sibling_groups.py --family-name-check data/elo-baptisms-before-1811.nt work/siblings-checked familyname=work/familyname/$R familyname-std=work/familyname-std/$R patronym=work/patronym/$R patronym-std=work/patronym-std/$R
```

## Baptisms to marriages

The parents of every baptism are linked to the bride and groom of the ELO DTB marriages (`between_b_m`, father = groom, mother = bride), with standardised given names and family name or patronym. The full dump has the names but its marriage records have no type or date; `data/dtb_trouwen.nt.gz` adds both (the marriage date, otherwise the ondertrouw date). Places come from `data/oa-pico-toponiemen.nt.gz` (IISG toponyms).

```bash
scripts/select_marriages.sh data/elo-pico.nt.gz data/dtb_trouwen.nt.gz data/elo-marriages-before-1811.nt
python3 scripts/standardise_given_names.py ../elo-dtb/lookup-tables/bloothooft-given-names.nt.gz data/elo-marriages-before-1811.nt data/elo-marriages-before-1811-std.nt
cat data/elo-baptisms-before-1811-std.nt data/elo-marriages-before-1811-std.nt > data/elo-baptisms-marriages-std.nt
scripts/run.sh marriages-familyname-std data/elo-baptisms-marriages-std.nt work/m-familyname-std
scripts/run.sh marriages-patronym-std data/elo-baptisms-marriages-std.nt work/m-patronym-std
python3 scripts/sibling_marriages.py work/sibling-marriages work/siblings-checked-groups.csv data/oa-pico-toponiemen.nt.gz data/dtb_trouwen.nt.gz familyname-std=work/m-familyname-std/$R patronym-std=work/m-patronym-std/$R
```

`work/sibling-marriages-links.csv` has every baptism–marriage link with both places; `work/sibling-marriages-groups.csv` says per sibling group whether its baptisms point to one marriage, several or none.

## Religion

`data/elo-religion.nt.gz` gives the denomination of each baptism (`picom:hasReligion` on the baptised child, IISG TaxonomyOfReligions); 94% of the baptisms have one. Siblings were usually baptised in the same church, so groups that mix denominations deserve a check:

```bash
python3 scripts/sibling_religion.py data/elo-religion.nt.gz work/siblings-checked-groups.csv work/siblings-religion.csv
```

909 of the 53,999 groups mix denominations: 1–2% of the groups with up to 9 baptisms, but 34% of those with 15 or more, which matches the groups joined through patronym-only links.

## Visualisations

- [viz/threads-of-leiden/](viz/threads-of-leiden/): every baptism as a point and every sibling link as a thread, 1600–1810, with lightning on families coloured by church of baptism, the parents' marriage and the birth places of bride and groom. "Trots op Zeeland" switches to the Zeeland view: brides and grooms born in Zeeland, on a map and as families.
- [viz/family-browser/](viz/family-browser/): a sample of sibling groups, each drawn as four networks (one per run), with pair-by-pair comparison.

Both read their data files with `fetch`, so serve the folder instead of opening the file:

```bash
python3 -m http.server 8000 --directory viz/threads-of-leiden
```

The data files are made by the scripts in [viz/build/](viz/build/) (run from the repository root, after the steps above); `zeeland_query.py` runs the Zeeland query on the ELO endpoint. Map coordinates in the Zeeland view are approximate, per municipality.

## Test

[tests/fixtures/invented-siblings.ttl](tests/fixtures/invented-siblings.ttl) has three **invented** baptisms for the parents of one real record. Run it together with that record:

```bash
mkdir -p work/fixture && cp ../elo-dtb/sample/a6ef5889-136b-b800-6747-c8eacbd459a1.ttl tests/fixtures/invented-siblings.ttl work/fixture/
python3 scripts/merge_ttl.py work/fixture data/test-siblings.nt
scripts/run.sh siblings data/test-siblings.nt work/test
```

Expected: `test-1` (spelling variants) links to the real record, `test-2` (32 years later) is rejected by the time rule, and `test-3` (other mother) does not link.

## Status

Tested on the extended elo-dtb sample (395 records, elo-dtb `8166a65`). `siblings`: 227 baptisms are indexed and all 225 links that pass are self-links. `marriages`: 88 of the 90 marriage records have a usable date and 1 baptism links to a marriage (Riebeek, ondertrouw 1787, baptism 1792); no sibling groups yet, see [docs/analysis-marriages.md](docs/analysis-marriages.md). `within-bm`: 0 links when a parent must match too, 4 links on names only, of which 3 are wrong and 1 is doubtful; the Bloothooft gender gives the same result, see [docs/analysis-within-bm.md](docs/analysis-within-bm.md). The known siblings in the sample (the Kloeck children of 1651 and 1655) are not linked yet; see [docs/analysis-kloeck-siblings.md](docs/analysis-kloeck-siblings.md) for why. Two baptisms are dropped because their date is only a year and month (`xsd:gYearMonth`), which burgerLinker cannot read.

Full ELO set: 395,690 baptisms before 1811. On the baptisms of 1700–1704 (12,913) the union of the four runs gives 3,483 sibling pairs in 1,991 groups; standardising the given names adds about a fifth more pairs. Common patronyms ("Pieter Jansz & Marij Jans") join different couples into one group, so the groups need checks before use; see [docs/analysis-full-baptisms.md](docs/analysis-full-baptisms.md).

Full runs (all 395,690 baptisms): 461,523 sibling pairs in 53,839 groups; with the family-name check 454,394 pairs in 53,999 groups. Most small and medium groups are plausible; most groups of 15 or more baptisms join different couples through patronym-only links, which still needs a fix. Baptisms to marriages: 174,588 DTB marriages before 1811; 130,237 baptisms (33%) link to 52,456 marriages, and 21,636 sibling groups point to one marriage. Most groups that point to several marriages have two records of the same couple within a year (ondertrouw and marriage). The analysis document does not yet cover the full runs and the marriages.
