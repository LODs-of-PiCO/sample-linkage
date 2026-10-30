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

There are four set-ups:

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
