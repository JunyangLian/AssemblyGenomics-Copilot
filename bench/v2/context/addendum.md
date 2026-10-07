
# C2 shared QC interpretation guidance

## Disposition and downstream use

Decide whether the delivered files can be consumed correctly before interpreting a quality statistic. A broken format or unresolved cross-file connection requires blocking consumption until repaired and validated. A completed analysis whose results are unreliable requires returning to the affected analysis step and regenerating the delivery. A usable result with a documented limitation may warrant a warning. Explain the relevant downstream consequence. Do not choose a disposition solely because a number is high or low. Distinguish a demonstrated failure from an optional additional diagnostic that has not been supplied.

## Database and run context

Evaluate a database version against the recorded run date, project specification and compatibility requirements. Do not infer obsolescence from an internally remembered latest release. A pinned version does not excuse incompatible inputs or failure to meet a stated requirement. State what the supplied version record establishes and what remains unknown.

## Coverage and identifier connections

For annotation coverage, identify the actual query set, unique identifiers, annotation flags, join operation and denominator. Compare the row-level annotations to the joined statistics. Missing annotation content with valid connections and rich annotations that cannot be connected to their queries require different remedies. Do not silently strip suffixes or rewrite identifiers without an unambiguous mapping and a subsequent connection check. Count distinct queries, not merely rows.

## Coding features and protein delivery

CDS feature rows represent coding segments; a protein can legitimately correspond to several rows. Distinguish CDS segments, transcripts, coding gene loci and unique protein identifiers. Check the parent-child hierarchy and the connection between CDS protein references and complete FAA records. A surplus of CDS rows alone does not establish extra genes, missing proteins or damaged annotation. An unresolved protein-reference connection must be repaired before extraction or downstream interpretation.

## Species and metric definitions

Interpret percentages using their actual biological unit, denominator, analysis mode and species context. Do not equate a fragment's proportion with a whole-genome measurement, or a transposable-element estimate with all masked bases. Do not manufacture a mandatory rejection threshold for a valid delivery merely because an additional optional metric is absent. Preserve nucleotide identity when downstream analyses require soft masking; compare case-insensitive sequence content as well as length and masking counts.
