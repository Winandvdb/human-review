# Our `openapi-diff.py` vs oasdiff — the eval behind dropping our differ

_Run on 7 Oct 2026 with oasdiff **1.33.0** (latest release, 1 Oct 2026) and the last version of `openapi-diff.py` before it was deleted._

**Question (Victor):** why do we keep our own OpenAPI differ next to oasdiff — does it gain anything, or is it reinventing the wheel?

**Answer:** it gains almost nothing and costs a lot. On 110 spec pairs with a clear verdict, oasdiff misses 5 that ours catches, ours misses 31 that oasdiff catches, and ours raises 15 false alarms against oasdiff's 2. Of the 5 only ours saw, the 2 clear ones were filed on oasdiff, the 3 arguable ones went to Victor by mail; oasdiff is now the API tab's single source. Besides those, the eval turned up 3 more oasdiff misses that ours missed too, filed as well — 5 issues in all, #1280–#1284; the other gaps both missed were already tracked upstream (#1054, #1163, #1164, #1175).

## Why ours existed

`openapi-diff.py` (Aug 2026, commit `03ca03d`) came first, before any third-party differ was wired in: a generic leaf-by-leaf walk of the two YAML trees plus a `classify()` table. The Java OpenAPITools/openapi-diff was added the next day as "the reference implementation", and when it turned out not to follow `$ref`s (4 of 11 affected operations listed), oasdiff replaced it as the engine (`c890f25`). From then on ours only fed the *cross-check*: the band said "checked by oasdiff and our openapi-diff.py" and turned red as **Verdict disputed** when the two disagreed. The recorded disagreements were all ours being wrong — counting one replaced schema as 3 breaking changes (`fold_replaced_shapes`), 6 vs 1 breaking before WARN+ counting.

## What ours checked (every rule)

- operation added → additive; removed → breaking; whole response code added → additive, removed → breaking
- any leaf under an operation or schema: `$ref`/`type`/`format` changed → breaking; `$ref`+`type`+`items` moving together → one breaking "replaced"
- `minimum`/`minLength`/`minItems`/`exclusiveMinimum`/`multipleOf` up → breaking, down → additive; `maximum`/`maxLength`/`maxItems`/`exclusiveMaximum` down → breaking, up → additive — **regardless of request/response direction**
- `enum` value removed → breaking, added → additive — regardless of direction
- `nullable`/`readOnly`/`writeOnly`/`default`/`operationId`/`deprecated` changed → "changed" (never breaking)
- any other leaf added → additive, removed → breaking; docs keys (`description`, `example`, …) → cosmetic
- `components.schemas`: schema added → additive, removed → breaking (even if unused); property added → breaking only if required **and** the schema is reachable from a request; property removed → breaking; property became required → breaking if request-side; required dropped → additive
- not looked at: `parameters` (a list, compared as one opaque leaf → "changed"), path-level parameters, `components.parameters/responses/requestBodies/securitySchemes`, top-level `security`, `servers`

## Results

| class | cases |
|---|---|
| both right | 46 |
| only ours catches | 5 |
| only oasdiff catches | 31 |
| both miss | 13 |
| ours false alarm | 13 |
| oasdiff false alarm | 0 |
| both false alarm | 2 |
| policy | 11 |
| **total** | **121** |

Expected verdict: **B** breaking, **N** not breaking, **?** arguable (policy). oasdiff verdict is `oasdiff breaking` (ERR+WARN) with default flags; `--flatten-allof --include-path-params` changed one case (path-param rename becomes breaking). Ours = any change classified breaking.

### Only ours catches → reported upstream

- **req-format-changed** — NewPet.born format date → date-time. oasdiff: `request-property-type-generalized`. → [#1281](https://github.com/oasdiff/oasdiff/issues/1281)
- **req-discriminator-mapping-changed** — PaymentIn mapping value `card` → `CARD`. oasdiff: `request-body-discriminator-mapping-added`, `request-body-discriminator-mapping-deleted`. → emailed (doubtful)
- **resp-enum-removed** — Pet.status enum constraint dropped (any string). oasdiff: `response-property-enum-value-removed`. → [#1280](https://github.com/oasdiff/oasdiff/issues/1280)
- **resp-discriminator-mapping-changed** — PaymentOut mapping value `card` → `CARD`. oasdiff: `response-body-discriminator-mapping-added`, `response-body-discriminator-mapping-deleted`. → emailed (doubtful)
- **resp-media-renamed** — GET /pets/{id} application/json → application/vnd.pet+json. oasdiff: `response-media-type-name-specialized`. → emailed (doubtful)

### Both miss (oasdiff gaps ours did not see either)

- **req-additionalprops-false** — NewPet gains additionalProperties: false. oasdiff: nothing. → known: [#1054](https://github.com/oasdiff/oasdiff/issues/1054)
- **req-discriminator-renamed** — PaymentIn discriminator propertyName kind → type. oasdiff: `request-body-discriminator-property-name-changed`. → emailed (doubtful)
- **resp-required-became-writeonly** — Pet.name (required) becomes writeOnly. oasdiff: `response-required-property-became-write-only`. → [#1282](https://github.com/oasdiff/oasdiff/issues/1282)
- **resp-discriminator-renamed** — PaymentOut discriminator propertyName kind → type. oasdiff: `response-body-discriminator-property-name-changed`. → emailed (doubtful)
- **query-explode-changed** — GET /pets `ids` explode true → false. oasdiff: nothing. → known: [#1164](https://github.com/oasdiff/oasdiff/issues/1164)
- **query-style-changed** — GET /pets `ids` style form → pipeDelimited. oasdiff: nothing. → known: [#1164](https://github.com/oasdiff/oasdiff/issues/1164)
- **path-level-param-became-required** — path-level optional `tenant` becomes required. oasdiff: nothing. → known: [#1163](https://github.com/oasdiff/oasdiff/issues/1163)
- **op-security-added** — GET /pets/{id} (anonymous) now requires apiKey. oasdiff: `api-security-added`. → [#1283](https://github.com/oasdiff/oasdiff/issues/1283)
- **global-security-added** — top-level security: apiKey added (ops had none). oasdiff: `api-global-security-added`. → [#1283](https://github.com/oasdiff/oasdiff/issues/1283)
- **apikey-header-renamed** — apiKey scheme header X-API-Key → X-Token (used by GET /pets). oasdiff: nothing. → known: [#1175](https://github.com/oasdiff/oasdiff/issues/1175)
- **security-scheme-type-changed** — apiKey scheme replaced by http bearer (same name, used by GET /pets). oasdiff: `api-security-component-type-changed`. → [#1284](https://github.com/oasdiff/oasdiff/issues/1284)
- **req-not-added** — NewPet.code gains not: {enum: [admin]}. oasdiff: nothing. → known: [#1054](https://github.com/oasdiff/oasdiff/issues/1054)
- **resp-additionalprops-schema-widened** — Owner gains additionalProperties: true where it had false. oasdiff: nothing. → known: [#1054](https://github.com/oasdiff/oasdiff/issues/1054)

### Only oasdiff catches

`request-body-required`, `req-pattern-added`, `req-became-enum`, `req-nullable-removed`, `req-uniqueitems-set`, `resp-prop-became-optional`, `resp-maxlength-increased`, `resp-maximum-increased`, `resp-minimum-decreased`, `resp-enum-value-added`, `resp-nullable-added`, `resp-oneof-added`, `query-required-added`, `query-became-required`, `query-type-changed`, `query-max-decreased`, `query-enum-value-removed`, `header-required-added`, `header-became-required`, `cookie-required-added`, `path-param-type-narrowed`, `path-level-param-required-added`, `component-param-became-required`, `security-scope-added`, `resp-header-became-optional`, `req-multipleof-set`, `req-minitems-set`, `req-anyof-removed`, `resp-allof-part-removed`, `oas31-req-const-added`, `query-required-with-default`

### False alarms

- ours false alarm: **path-param-renamed** — /pets/{id} → /pets/{petId} (same position, same type)
- ours false alarm: **error-status-removed** — GET /pets/{id} no longer documents 404
- ours false alarm: **req-type-widened** — NewPet.weight integer → number
- ours false alarm: **resp-maxlength-decreased** — Pet.name maxLength 50 → 20
- ours false alarm: **resp-minimum-increased** — Pet.age minimum 0 → 1
- ours false alarm: **resp-enum-value-removed** — Pet.status enum loses `sold`
- ours false alarm: **resp-oneof-removed** — PaymentOut oneOf loses Cash
- ours false alarm: **resp-header-optional-removed** — 201 loses optional X-Rate header
- ours false alarm: **schema-renamed** — components.schemas.Owner renamed to Person (same shape)
- ours false alarm: **ref-inlined** — Pet.owner $ref replaced by the identical inline schema
- ours false alarm: **unused-schema-removed** — components.schemas.Unused (referenced nowhere) removed
- ours false alarm: **unused-schema-changed** — components.schemas.Unused.x string → integer
- both false alarm: **security-scheme-removed** — POST /pets security requirement removed → [#1283](https://github.com/oasdiff/oasdiff/issues/1283)
- ours false alarm: **resp-maxitems-set-then-raised** — Pet.tags gains maxItems 5 (response narrowing)
- both false alarm: **req-enum-removed** — NewPet.status enum constraint dropped (any string) → [#1280](https://github.com/oasdiff/oasdiff/issues/1280)

### Full table

| case | change | exp | oasdiff | ours | class | oasdiff rule ids (ERR/WARN; info) | upstream |
|---|---|---|---|---|---|---|---|
| op-removed | DELETE /pets/{id} removed | B | B | B | both right | `api-removed-without-deprecation` |  |
| op-added | PUT /pets/{id} added | N | N | N | both right | info: `endpoint-added` |  |
| path-renamed | /pets/{id} moved to /animals/{id} | B | B | B | both right | `api-path-removed-without-deprecation`; info: `endpoint-added` |  |
| path-param-renamed | /pets/{id} → /pets/{petId} (same position, same type) | N | N | B | ours false alarm |  |  |
| method-changed | DELETE /pets/{id} → POST /pets/{id} | B | B | B | both right | `api-removed-without-deprecation`; info: `endpoint-added` |  |
| op-deprecated | GET /pets/{id} marked deprecated | N | N | N | both right | info: `endpoint-deprecated` |  |
| operation-id-changed | operationId getPet → fetchPet | ? | N | N | policy | info: `api-operation-id-removed` | emailed (doubtful) |
| success-status-removed | GET /pets/{id} 200 → 203 only | B | B | B | both right | `response-success-status-removed`; info: `response-success-status-added` |  |
| error-status-removed | GET /pets/{id} no longer documents 404 | N | N | B | ours false alarm | info: `response-non-success-status-removed` |  |
| error-status-added | GET /pets/{id} documents a new 409 | ? | N | N | policy | info: `response-non-success-status-added` |  |
| response-media-removed | GET /pets/{id} stops producing application/xml | B | B | B | both right | `response-media-type-removed` |  |
| request-media-removed | POST /pets stops consuming application/xml | B | B | B | both right | `request-body-media-type-removed` |  |
| request-body-required | POST /payments body was optional, now required | B | B | N | only oasdiff catches | `request-body-became-required` |  |
| req-required-prop-added | NewPet gains required `species` | B | B | B | both right | `new-required-request-property` |  |
| req-optional-prop-added | NewPet gains optional `species` | N | N | N | both right | info: `new-optional-request-property` |  |
| req-prop-became-required | NewPet.tag becomes required | B | B | B | both right | `request-property-became-required` |  |
| req-prop-became-optional | NewPet.name no longer required | N | N | N | both right | info: `request-property-became-optional` |  |
| req-prop-removed | NewPet.tag removed | ? | B | B | policy | `request-property-removed` |  |
| req-type-changed | NewPet.weight integer → string | B | B | B | both right | `request-property-type-changed`; info: `request-property-type-compatible` |  |
| req-type-widened | NewPet.weight integer → number | N | N | B | ours false alarm | info: `request-property-type-generalized` |  |
| req-format-changed | NewPet.born format date → date-time | B | N | B | only ours catches | info: `request-property-type-generalized` | [#1281](https://github.com/oasdiff/oasdiff/issues/1281) |
| req-format-added | NewPet.code gains format: uuid | B | B | B | both right | `request-property-type-changed` |  |
| req-maxlength-decreased | NewPet.name maxLength 50 → 20 | B | B | B | both right | `request-property-max-length-decreased` |  |
| req-maxlength-increased | NewPet.name maxLength 50 → 100 | N | N | N | both right | info: `request-property-max-length-increased` |  |
| req-minlength-increased | NewPet.name minLength 1 → 3 | B | B | B | both right | `request-property-min-length-increased` |  |
| req-maximum-decreased | NewPet.age maximum 30 → 20 | B | B | B | both right | `request-property-max-decreased` |  |
| req-minimum-decreased | NewPet.age minimum 0 → -1 | N | N | N | both right | info: `request-property-min-decreased` |  |
| req-maxlength-set | NewPet.code gains maxLength 8 | B | B | B | both right | `request-property-max-length-set` |  |
| req-pattern-added | NewPet.code gains pattern ^[A-Z]+$ | B | B | N | only oasdiff catches | `request-property-pattern-added` |  |
| req-enum-value-removed | NewPet.status enum loses `sold` | B | B | B | both right | `request-property-enum-value-removed` |  |
| req-enum-value-added | NewPet.status enum gains `pending` | N | N | N | both right | info: `request-property-enum-value-added` |  |
| req-became-enum | NewPet.tag becomes enum [a, b] | B | B | N | only oasdiff catches | `request-property-became-enum`; info: `request-property-enum-value-added` |  |
| req-nullable-removed | NewPet.nickname no longer nullable | B | B | N | only oasdiff catches | `request-property-became-not-nullable` |  |
| req-nullable-added | NewPet.tag becomes nullable | N | N | N | both right | info: `request-property-became-nullable` |  |
| req-maxitems-decreased | NewPet.tags maxItems 10 → 3 | B | B | B | both right | `request-property-max-items-decreased` |  |
| req-uniqueitems-set | NewPet.tags gains uniqueItems: true | B | B | N | only oasdiff catches | `request-property-unique-items-set` |  |
| req-items-type-changed | NewPet.tags items string → integer | B | B | B | both right | `request-property-type-changed` |  |
| req-additionalprops-false | NewPet gains additionalProperties: false | B | N | N | both miss |  | known: [#1054](https://github.com/oasdiff/oasdiff/issues/1054) |
| req-default-changed | NewPet.notes default 'none' → '' | ? | N | N | policy | info: `request-property-default-value-changed` |  |
| req-prop-became-readonly | NewPet.tag becomes readOnly | ? | N | N | policy | info: `request-optional-property-became-read-only` | emailed (doubtful) |
| req-required-prop-readonly | NewPet.name (required) becomes readOnly | ? | N | N | policy | info: `request-required-property-became-read-only` | emailed (doubtful) |
| req-allof-added | NewPet wrapped in allOf with a required `species` | B | B | B | both right | `request-body-all-of-added`, `request-property-removed`; info: `request-body-type-generalized` |  |
| req-oneof-removed | PaymentIn oneOf loses Cash | B | B | B | both right | `request-body-one-of-removed`; info: `request-body-discriminator-mapping-deleted` |  |
| req-oneof-added | PaymentIn oneOf gains Voucher | N | N | N | both right | info: `request-body-discriminator-mapping-added`, `request-body-one-of-added` |  |
| req-discriminator-renamed | PaymentIn discriminator propertyName kind → type | B | N | N | both miss | info: `request-body-discriminator-property-name-changed` | emailed (doubtful) |
| req-discriminator-mapping-changed | PaymentIn mapping value `card` → `CARD` | B | N | B | only ours catches | info: `request-body-discriminator-mapping-added`, `request-body-discriminator-mapping-deleted` | emailed (doubtful) |
| resp-required-prop-removed | Pet.status (required) removed | B | B | B | both right | `response-required-property-removed` |  |
| resp-optional-prop-removed | Pet.tag (optional) removed | ? | N | B | policy | info: `response-optional-property-removed` |  |
| resp-prop-became-optional | Pet.name no longer required | B | B | N | only oasdiff catches | `response-property-became-optional` |  |
| resp-prop-became-required | Pet.tag becomes required | N | N | N | both right | info: `response-property-became-required` |  |
| resp-optional-prop-added | Pet gains optional `color` | N | N | N | both right | info: `response-optional-property-added` |  |
| resp-required-prop-added | Pet gains required `color` | N | N | N | both right | info: `response-required-property-added` |  |
| resp-type-changed | Pet.age integer → string | B | B | B | both right | `response-property-max-unset`, `response-property-min-unset`, `response-property-type-changed` |  |
| resp-type-widened | Pet.age integer → number | B | B | B | both right | `response-property-type-generalized` |  |
| resp-format-widened | Pet.id format int64 → none (unbounded integer) | ? | B | B | policy | `response-property-type-changed` |  |
| resp-format-changed | Pet.born format date → date-time | B | B | B | both right | `response-property-type-changed` |  |
| resp-maxlength-increased | Pet.name maxLength 50 → 100 | B | B | N | only oasdiff catches | `response-property-max-length-increased` |  |
| resp-maxlength-decreased | Pet.name maxLength 50 → 20 | N | N | B | ours false alarm | info: `response-property-max-length-decreased` |  |
| resp-maximum-increased | Pet.age maximum 30 → 99 | B | B | N | only oasdiff catches | `response-property-max-increased` |  |
| resp-minimum-decreased | Pet.age minimum 0 → -1 | B | B | N | only oasdiff catches | `response-property-min-decreased` |  |
| resp-minimum-increased | Pet.age minimum 0 → 1 | N | N | B | ours false alarm | info: `response-property-min-increased` |  |
| resp-enum-value-added | Pet.status enum gains `pending` | B | B | N | only oasdiff catches | `response-property-enum-value-added` |  |
| resp-enum-value-removed | Pet.status enum loses `sold` | N | N | B | ours false alarm | info: `response-property-enum-value-removed` |  |
| resp-enum-removed | Pet.status enum constraint dropped (any string) | B | N | B | only ours catches | info: `response-property-enum-value-removed` | [#1280](https://github.com/oasdiff/oasdiff/issues/1280) |
| resp-nullable-added | Pet.name becomes nullable | B | B | N | only oasdiff catches | `response-property-became-nullable` |  |
| resp-items-type-changed | Pet.tags items string → integer | B | B | B | both right | `response-property-type-changed`; info: `response-property-type-compatible` |  |
| resp-required-became-writeonly | Pet.name (required) becomes writeOnly | B | N | N | both miss | info: `response-required-property-became-write-only` | [#1282](https://github.com/oasdiff/oasdiff/issues/1282) |
| resp-nested-ref-prop-removed | Owner.ownerId (required, reached via Pet.owner) removed | B | B | B | both right | `response-required-property-removed` |  |
| resp-oneof-added | PaymentOut oneOf gains Voucher | B | B | N | only oasdiff catches | `response-body-one-of-added`; info: `response-body-discriminator-mapping-added` |  |
| resp-oneof-removed | PaymentOut oneOf loses Cash | N | N | B | ours false alarm | info: `response-body-discriminator-mapping-deleted`, `response-body-one-of-removed` |  |
| resp-discriminator-renamed | PaymentOut discriminator propertyName kind → type | B | N | N | both miss | info: `response-body-discriminator-property-name-changed` | emailed (doubtful) |
| resp-discriminator-mapping-changed | PaymentOut mapping value `card` → `CARD` | B | N | B | only ours catches | info: `response-body-discriminator-mapping-added`, `response-body-discriminator-mapping-deleted` | emailed (doubtful) |
| resp-header-removed | 201 loses required Location header | B | B | B | both right | `required-response-header-removed` |  |
| resp-header-optional-removed | 201 loses optional X-Rate header | N | N | B | ours false alarm | info: `optional-response-header-removed` |  |
| resp-header-type-changed | 201 X-Rate integer → string | B | B | B | both right | `response-header-type-changed` |  |
| schema-renamed | components.schemas.Owner renamed to Person (same shape) | N | N | B | ours false alarm | info: `api-schema-removed` |  |
| ref-inlined | Pet.owner $ref replaced by the identical inline schema | N | N | B | ours false alarm |  |  |
| unused-schema-removed | components.schemas.Unused (referenced nowhere) removed | N | N | B | ours false alarm | info: `api-schema-removed` |  |
| unused-schema-changed | components.schemas.Unused.x string → integer | N | N | B | ours false alarm |  |  |
| description-changed | Pet.name gains a description | N | N | N | both right |  |  |
| query-required-added | GET /pets gains required query `owner` | B | B | N | only oasdiff catches | `new-required-request-parameter` |  |
| query-optional-added | GET /pets gains optional query `owner` | N | N | N | both right | info: `new-optional-request-parameter` |  |
| query-became-required | GET /pets `limit` becomes required | B | B | N | only oasdiff catches | `request-parameter-became-required` |  |
| query-removed | GET /pets drops `status` | ? | B | N | policy | `request-parameter-removed` |  |
| query-type-changed | GET /pets `limit` integer → boolean | B | B | N | only oasdiff catches | `request-parameter-type-changed`; info: `request-parameter-max-unset`, `request-parameter-min-unset` |  |
| query-max-decreased | GET /pets `limit` maximum 100 → 50 | B | B | N | only oasdiff catches | `request-parameter-max-decreased` |  |
| query-enum-value-removed | GET /pets `status` enum loses `sold` | B | B | N | only oasdiff catches | `request-parameter-enum-value-removed` |  |
| query-explode-changed | GET /pets `ids` explode true → false | B | N | N | both miss |  | known: [#1164](https://github.com/oasdiff/oasdiff/issues/1164) |
| query-style-changed | GET /pets `ids` style form → pipeDelimited | B | N | N | both miss |  | known: [#1164](https://github.com/oasdiff/oasdiff/issues/1164) |
| header-required-added | GET /pets gains required header X-Tenant | B | B | N | only oasdiff catches | `new-required-request-parameter` |  |
| header-became-required | GET /pets header X-Trace becomes required | B | B | N | only oasdiff catches | `request-parameter-became-required` |  |
| cookie-required-added | GET /pets gains required cookie `session` | B | B | N | only oasdiff catches | `new-required-request-parameter` |  |
| path-param-type-narrowed | GET /payments/{pid} pid string → integer | B | B | N | only oasdiff catches | `request-parameter-type-changed` |  |
| path-level-param-required-added | path-level required query `tenant` on /pets/{id} | B | B | N | only oasdiff catches | `new-required-request-default-parameter-to-existing-path` |  |
| path-level-param-became-required | path-level optional `tenant` becomes required | B | N | N | both miss |  | known: [#1163](https://github.com/oasdiff/oasdiff/issues/1163) |
| component-param-became-required | components.parameters.Limit (via $ref) becomes required | B | B | N | only oasdiff catches | `request-parameter-became-required` |  |
| op-security-added | GET /pets/{id} (anonymous) now requires apiKey | B | N | N | both miss | info: `api-security-added` | [#1283](https://github.com/oasdiff/oasdiff/issues/1283) |
| global-security-added | top-level security: apiKey added (ops had none) | B | N | N | both miss | info: `api-global-security-added` | [#1283](https://github.com/oasdiff/oasdiff/issues/1283) |
| security-scope-added | POST /pets needs pets:admin besides pets:write | B | B | N | only oasdiff catches | `api-security-scope-added` |  |
| security-scheme-removed | POST /pets security requirement removed | N | B | B | both false alarm | `api-security-removed` | [#1283](https://github.com/oasdiff/oasdiff/issues/1283) |
| apikey-header-renamed | apiKey scheme header X-API-Key → X-Token (used by GET /pets) | B | N | N | both miss |  | known: [#1175](https://github.com/oasdiff/oasdiff/issues/1175) |
| security-scheme-type-changed | apiKey scheme replaced by http bearer (same name, used by GET /pets) | B | N | N | both miss | info: `api-security-component-type-changed` | [#1284](https://github.com/oasdiff/oasdiff/issues/1284) |
| oauth-token-url-changed | oauth tokenUrl moved | ? | N | N | policy |  | emailed: non-implicit OAuth flows never diffed |
| server-basepath-changed | servers url /v1 → /v2 | ? | N | N | policy |  |  |
| resp-header-became-optional | 201 Location header no longer required | B | B | N | only oasdiff catches | `response-header-became-optional` |  |
| req-multipleof-set | NewPet.weight gains multipleOf: 5 | B | B | N | only oasdiff catches | `request-property-multiple-of-set` |  |
| req-minitems-set | NewPet.tags gains minItems: 1 | B | B | N | only oasdiff catches | `request-property-min-items-set` |  |
| resp-maxitems-set-then-raised | Pet.tags gains maxItems 5 (response narrowing) | N | N | B | ours false alarm | info: `response-property-max-items-set` |  |
| resp-body-type-changed | GET /pets returns an object page instead of an array | B | B | B | both right | `response-body-type-changed`; info: `response-optional-property-added` |  |
| req-body-schema-swapped | POST /pets body NewPet → Pet (requires id, status) | B | B | B | both right | `new-required-request-property`, `request-property-became-required`, `request-property-removed`; info: `new-optional-request-property`, `request-property-max-items-unset`, `request-property-min-length-unset` |  |
| resp-media-renamed | GET /pets/{id} application/json → application/vnd.pet+json | B | N | B | only ours catches | info: `response-media-type-name-specialized` | emailed (doubtful) |
| resp-anyof-added | Pet.tag string → anyOf [string, integer] | B | B | B | both right | `response-property-list-of-types-widened` |  |
| req-anyof-removed | NewPet.weight anyOf [integer, string] → anyOf [integer] | B | B | N | only oasdiff catches | `request-property-list-of-types-narrowed` |  |
| resp-allof-part-removed | Pet = allOf [Base, Extra] loses Extra (required `status`) | B | B | N | only oasdiff catches | `response-body-all-of-removed`, `response-property-all-of-removed` |  |
| resp-required-became-readonly | Pet.name (required) becomes readOnly | N | N | N | both right | info: `response-required-property-became-read-only` |  |
| oas31-resp-null-added | 3.1: Pet.tag type string → [string, null] | B | B | B | both right | `response-property-became-nullable` |  |
| oas31-req-const-added | 3.1: NewPet.status gains const: available | B | B | N | only oasdiff catches | `request-property-const-added` |  |
| req-not-added | NewPet.code gains not: {enum: [admin]} | B | N | N | both miss |  | known: [#1054](https://github.com/oasdiff/oasdiff/issues/1054) |
| resp-additionalprops-schema-widened | Owner gains additionalProperties: true where it had false | B | N | N | both miss |  | known: [#1054](https://github.com/oasdiff/oasdiff/issues/1054) |
| query-required-with-default | GET /pets gains required query `sort` with default | B | B | N | only oasdiff catches | `new-required-request-parameter` |  |
| req-enum-removed | NewPet.status enum constraint dropped (any string) | N | B | B | both false alarm | `request-property-enum-value-removed` | [#1280](https://github.com/oasdiff/oasdiff/issues/1280) |

## Corpus

Every pair is the base spec below plus one mutation. To re-run: save base/head, then `oasdiff breaking base.yaml head.yaml` (and `oasdiff changelog … -f json` for the info entries).

<details><summary>Base spec</summary>

```yaml
openapi: 3.0.3
info:
  title: Pets
  version: 1.0.0
paths:
  /pets:
    get:
      operationId: listPets
      parameters:
      - name: limit
        in: query
        required: false
        schema:
          type: integer
          minimum: 1
          maximum: 100
      - name: status
        in: query
        schema:
          type: string
          enum:
          - available
          - sold
      - name: ids
        in: query
        style: form
        explode: true
        schema:
          type: array
          items:
            type: integer
      - name: X-Trace
        in: header
        required: false
        schema:
          type: string
      responses:
        '200':
          description: ok
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Pet'
    post:
      operationId: createPet
      security:
      - oauth:
        - pets:write
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NewPet'
          application/xml:
            schema:
              $ref: '#/components/schemas/NewPet'
      responses:
        '201':
          description: created
          headers:
            Location:
              required: true
              schema:
                type: string
            X-Rate:
              schema:
                type: integer
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Pet'
        '400':
          description: bad request
  /pets/{id}:
    get:
      operationId: getPet
      parameters:
      - name: id
        in: path
        required: true
        schema:
          type: integer
          format: int64
      responses:
        '200':
          description: ok
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Pet'
            application/xml:
              schema:
                $ref: '#/components/schemas/Pet'
        '404':
          description: not found
    delete:
      operationId: deletePet
      parameters:
      - name: id
        in: path
        required: true
        schema:
          type: integer
          format: int64
      responses:
        '204':
          description: gone
  /payments:
    post:
      operationId: pay
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PaymentIn'
      responses:
        '204':
          description: paid
  /payments/{pid}:
    get:
      operationId: getPayment
      parameters:
      - name: pid
        in: path
        required: true
        schema:
          type: string
      responses:
        '200':
          description: ok
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaymentOut'
components:
  securitySchemes:
    apiKey:
      type: apiKey
      in: header
      name: X-API-Key
    oauth:
      type: oauth2
      flows:
        clientCredentials:
          tokenUrl: https://auth.example.com/token
          scopes:
            pets:write: write
            pets:admin: admin
  schemas:
    Pet:
      type: object
      required:
      - id
      - name
      - status
      properties:
        id:
          type: integer
          format: int64
        name:
          type: string
          maxLength: 50
        status:
          type: string
          enum:
          - available
          - sold
        tag:
          type: string
        age:
          type: integer
          minimum: 0
          maximum: 30
        born:
          type: string
          format: date
        tags:
          type: array
          items:
            type: string
        owner:
          $ref: '#/components/schemas/Owner'
    Owner:
      type: object
      required:
      - ownerId
      properties:
        ownerId:
          type: integer
        email:
          type: string
    NewPet:
      type: object
      required:
      - name
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 50
        status:
          type: string
          enum:
          - available
          - sold
        tag:
          type: string
        age:
          type: integer
          minimum: 0
          maximum: 30
        born:
          type: string
          format: date
        nickname:
          type: string
          nullable: true
        weight:
          type: integer
        tags:
          type: array
          maxItems: 10
          items:
            type: string
        code:
          type: string
        notes:
          type: string
          default: none
    Card:
      type: object
      required:
      - kind
      - number
      properties:
        kind:
          type: string
        number:
          type: string
    Cash:
      type: object
      required:
      - kind
      - amount
      properties:
        kind:
          type: string
        amount:
          type: number
    Voucher:
      type: object
      required:
      - kind
      - code
      properties:
        kind:
          type: string
        code:
          type: string
    PaymentIn:
      oneOf:
      - $ref: '#/components/schemas/Card'
      - $ref: '#/components/schemas/Cash'
      discriminator:
        propertyName: kind
        mapping:
          card: '#/components/schemas/Card'
          cash: '#/components/schemas/Cash'
    PaymentOut:
      oneOf:
      - $ref: '#/components/schemas/Card'
      - $ref: '#/components/schemas/Cash'
      discriminator:
        propertyName: kind
        mapping:
          card: '#/components/schemas/Card'
          cash: '#/components/schemas/Cash'
    Unused:
      type: object
      properties:
        x:
          type: string
```
</details>

<details><summary><b>op-removed</b> — DELETE /pets/{id} removed (expected B: callers of the operation get 404/405)</summary>

```diff
@@ -97,16 +97,4 @@
         '404':
           description: not found
-    delete:
-      operationId: deletePet
-      parameters:
-      - name: id
-        in: path
-        required: true
-        schema:
-          type: integer
-          format: int64
-      responses:
-        '204':
-          description: gone
   /payments:
     post:
```
</details>
<details><summary><b>op-added</b> — PUT /pets/{id} added (expected N: nobody calls it yet)</summary>

```diff
@@ -109,4 +109,16 @@
         '204':
           description: gone
+    put:
+      operationId: updatePet
+      parameters:
+      - name: id
+        in: path
+        required: true
+        schema:
+          type: integer
+          format: int64
+      responses:
+        '204':
+          description: ok
   /payments:
     post:
```
</details>
<details><summary><b>path-renamed</b> — /pets/{id} moved to /animals/{id} (expected B: old URL no longer served)</summary>

```diff
@@ -75,5 +75,33 @@
         '400':
           description: bad request
-  /pets/{id}:
+  /payments:
+    post:
+      operationId: pay
+      requestBody:
+        required: true
+        content:
+          application/json:
+            schema:
+              $ref: '#/components/schemas/PaymentIn'
+      responses:
+        '204':
+          description: paid
+  /payments/{pid}:
+    get:
+      operationId: getPayment
+      parameters:
+      - name: pid
+        in: path
+        required: true
+        schema:
+          type: string
+      responses:
+        '200':
+          description: ok
+          content:
+            application/json:
+              schema:
+                $ref: '#/components/schemas/PaymentOut'
+  /animals/{id}:
     get:
       operationId: getPet
@@ -109,32 +137,4 @@
         '204':
           description: gone
-  /payments:
-    post:
-      operationId: pay
-      requestBody:
-        required: true
-        content:
-          application/json:
-            schema:
-              $ref: '#/components/schemas/PaymentIn'
-      responses:
-        '204':
-          description: paid
-  /payments/{pid}:
-    get:
-      operationId: getPayment
-      parameters:
-      - name: pid
-        in: path
-        required: true
-        schema:
-          type: string
-      responses:
-        '200':
-          description: ok
-          content:
-            application/json:
-              schema:
-                $ref: '#/components/schemas/PaymentOut'
 components:
   securitySchemes:
```
</details>
<details><summary><b>path-param-renamed</b> — /pets/{id} → /pets/{petId} (same position, same type) (expected N: the wire URL is identical; only the template variable's name changed)</summary>

```diff
@@ -75,9 +75,37 @@
         '400':
           description: bad request
-  /pets/{id}:
+  /payments:
+    post:
+      operationId: pay
+      requestBody:
+        required: true
+        content:
+          application/json:
+            schema:
+              $ref: '#/components/schemas/PaymentIn'
+      responses:
+        '204':
+          description: paid
+  /payments/{pid}:
+    get:
+      operationId: getPayment
+      parameters:
+      - name: pid
+        in: path
+        required: true
+        schema:
+          type: string
+      responses:
+        '200':
+          description: ok
+          content:
+            application/json:
+              schema:
+                $ref: '#/components/schemas/PaymentOut'
+  /pets/{petId}:
     get:
       operationId: getPet
       parameters:
-      - name: id
+      - name: petId
         in: path
         required: true
@@ -100,5 +128,5 @@
       operationId: deletePet
       parameters:
-      - name: id
+      - name: petId
         in: path
         required: true
@@ -109,32 +137,4 @@
         '204':
           description: gone
-  /payments:
-    post:
-      operationId: pay
-      requestBody:
-        required: true
-        content:
-          application/json:
-            schema:
-              $ref: '#/components/schemas/PaymentIn'
-      responses:
-        '204':
-          description: paid
-  /payments/{pid}:
-    get:
-      operationId: getPayment
-      parameters:
-      - name: pid
-        in: path
-        required: true
-        schema:
-          type: string
-      responses:
-        '200':
-          description: ok
-          content:
-            application/json:
-              schema:
-                $ref: '#/components/schemas/PaymentOut'
 components:
   securitySchemes:
```
</details>
<details><summary><b>method-changed</b> — DELETE /pets/{id} → POST /pets/{id} (expected B: the old method is gone)</summary>

```diff
@@ -97,5 +97,5 @@
         '404':
           description: not found
-    delete:
+    post:
       operationId: deletePet
       parameters:
```
</details>
<details><summary><b>op-deprecated</b> — GET /pets/{id} marked deprecated (expected N: still served; a warning to clients)</summary>

```diff
@@ -97,4 +97,5 @@
         '404':
           description: not found
+      deprecated: true
     delete:
       operationId: deletePet
```
</details>
<details><summary><b>operation-id-changed</b> — operationId getPet → fetchPet (expected ?: wire-compatible, but every generated SDK renames the method — a source break for codegen clients)</summary>

```diff
@@ -77,5 +77,5 @@
   /pets/{id}:
     get:
-      operationId: getPet
+      operationId: fetchPet
       parameters:
       - name: id
```
</details>
<details><summary><b>success-status-removed</b> — GET /pets/{id} 200 → 203 only (expected B: clients expect 200)</summary>

```diff
@@ -86,5 +86,7 @@
           format: int64
       responses:
-        '200':
+        '404':
+          description: not found
+        '203':
           description: ok
           content:
@@ -95,6 +97,4 @@
               schema:
                 $ref: '#/components/schemas/Pet'
-        '404':
-          description: not found
     delete:
       operationId: deletePet
```
</details>
<details><summary><b>error-status-removed</b> — GET /pets/{id} no longer documents 404 (expected N: the server can still return it; a client handling 404 is not harmed by the doc losing it)</summary>

```diff
@@ -95,6 +95,4 @@
               schema:
                 $ref: '#/components/schemas/Pet'
-        '404':
-          description: not found
     delete:
       operationId: deletePet
```
</details>
<details><summary><b>error-status-added</b> — GET /pets/{id} documents a new 409 (expected ?: a new error code the client never handled — oasdiff and most policies call it non-breaking)</summary>

```diff
@@ -97,4 +97,6 @@
         '404':
           description: not found
+        '409':
+          description: conflict
     delete:
       operationId: deletePet
```
</details>
<details><summary><b>response-media-removed</b> — GET /pets/{id} stops producing application/xml (expected B: an XML client gets 406)</summary>

```diff
@@ -90,7 +90,4 @@
           content:
             application/json:
-              schema:
-                $ref: '#/components/schemas/Pet'
-            application/xml:
               schema:
                 $ref: '#/components/schemas/Pet'
```
</details>
<details><summary><b>request-media-removed</b> — POST /pets stops consuming application/xml (expected B: an XML client gets 415)</summary>

```diff
@@ -53,7 +53,4 @@
         content:
           application/json:
-            schema:
-              $ref: '#/components/schemas/NewPet'
-          application/xml:
             schema:
               $ref: '#/components/schemas/NewPet'
```
</details>
<details><summary><b>request-body-required</b> — POST /payments body was optional, now required (expected B: a client that sent no body is now rejected) _(base differs from the common one)_</summary>

```diff
@@ -113,5 +113,5 @@
       operationId: pay
       requestBody:
-        required: false
+        required: true
         content:
           application/json:
```
</details>
<details><summary><b>req-required-prop-added</b> — NewPet gains required `species` (expected B: old payloads lack it)</summary>

```diff
@@ -198,4 +198,5 @@
       required:
       - name
+      - species
       properties:
         name:
@@ -232,4 +233,6 @@
           type: string
           default: none
+        species:
+          type: string
     Card:
       type: object
```
</details>
<details><summary><b>req-optional-prop-added</b> — NewPet gains optional `species` (expected N: old payloads stay valid)</summary>

```diff
@@ -232,4 +232,6 @@
           type: string
           default: none
+        species:
+          type: string
     Card:
       type: object
```
</details>
<details><summary><b>req-prop-became-required</b> — NewPet.tag becomes required (expected B: payloads without tag rejected)</summary>

```diff
@@ -198,4 +198,5 @@
       required:
       - name
+      - tag
       properties:
         name:
```
</details>
<details><summary><b>req-prop-became-optional</b> — NewPet.name no longer required (expected N: accepts more)</summary>

```diff
@@ -196,6 +196,5 @@
     NewPet:
       type: object
-      required:
-      - name
+      required: []
       properties:
         name:
```
</details>
<details><summary><b>req-prop-removed</b> — NewPet.tag removed (expected ?: server ignores the unknown field unless it rejects unknown properties; oasdiff WARNs)</summary>

```diff
@@ -208,6 +208,4 @@
           - available
           - sold
-        tag:
-          type: string
         age:
           type: integer
```
</details>
<details><summary><b>req-type-changed</b> — NewPet.weight integer → string (expected B: a client sending 5 is rejected)</summary>

```diff
@@ -221,5 +221,5 @@
           nullable: true
         weight:
-          type: integer
+          type: string
         tags:
           type: array
```
</details>
<details><summary><b>req-type-widened</b> — NewPet.weight integer → number (expected N: every integer is a number: accepts more)</summary>

```diff
@@ -221,5 +221,5 @@
           nullable: true
         weight:
-          type: integer
+          type: number
         tags:
           type: array
```
</details>
<details><summary><b>req-format-changed</b> — NewPet.born format date → date-time (expected B: '2020-01-01' is no longer valid)</summary>

```diff
@@ -216,5 +216,5 @@
         born:
           type: string
-          format: date
+          format: date-time
         nickname:
           type: string
```
</details>
<details><summary><b>req-format-added</b> — NewPet.code gains format: uuid (expected B: free strings rejected)</summary>

```diff
@@ -229,4 +229,5 @@
         code:
           type: string
+          format: uuid
         notes:
           type: string
```
</details>
<details><summary><b>req-maxlength-decreased</b> — NewPet.name maxLength 50 → 20 (expected B: long names rejected)</summary>

```diff
@@ -202,5 +202,5 @@
           type: string
           minLength: 1
-          maxLength: 50
+          maxLength: 20
         status:
           type: string
```
</details>
<details><summary><b>req-maxlength-increased</b> — NewPet.name maxLength 50 → 100 (expected N: accepts more)</summary>

```diff
@@ -202,5 +202,5 @@
           type: string
           minLength: 1
-          maxLength: 50
+          maxLength: 100
         status:
           type: string
```
</details>
<details><summary><b>req-minlength-increased</b> — NewPet.name minLength 1 → 3 (expected B: short names rejected)</summary>

```diff
@@ -201,5 +201,5 @@
         name:
           type: string
-          minLength: 1
+          minLength: 3
           maxLength: 50
         status:
```
</details>
<details><summary><b>req-maximum-decreased</b> — NewPet.age maximum 30 → 20 (expected B: age 25 rejected)</summary>

```diff
@@ -213,5 +213,5 @@
           type: integer
           minimum: 0
-          maximum: 30
+          maximum: 20
         born:
           type: string
```
</details>
<details><summary><b>req-minimum-decreased</b> — NewPet.age minimum 0 → -1 (expected N: accepts more)</summary>

```diff
@@ -212,5 +212,5 @@
         age:
           type: integer
-          minimum: 0
+          minimum: -1
           maximum: 30
         born:
```
</details>
<details><summary><b>req-maxlength-set</b> — NewPet.code gains maxLength 8 (expected B: longer codes rejected)</summary>

```diff
@@ -229,4 +229,5 @@
         code:
           type: string
+          maxLength: 8
         notes:
           type: string
```
</details>
<details><summary><b>req-pattern-added</b> — NewPet.code gains pattern ^[A-Z]+$ (expected B: lowercase rejected)</summary>

```diff
@@ -229,4 +229,5 @@
         code:
           type: string
+          pattern: ^[A-Z]+$
         notes:
           type: string
```
</details>
<details><summary><b>req-enum-value-removed</b> — NewPet.status enum loses `sold` (expected B: 'sold' rejected)</summary>

```diff
@@ -207,5 +207,4 @@
           enum:
           - available
-          - sold
         tag:
           type: string
```
</details>
<details><summary><b>req-enum-value-added</b> — NewPet.status enum gains `pending` (expected N: accepts more)</summary>

```diff
@@ -208,4 +208,5 @@
           - available
           - sold
+          - pending
         tag:
           type: string
```
</details>
<details><summary><b>req-became-enum</b> — NewPet.tag becomes enum [a, b] (expected B: free text rejected)</summary>

```diff
@@ -210,4 +210,7 @@
         tag:
           type: string
+          enum:
+          - a
+          - b
         age:
           type: integer
```
</details>
<details><summary><b>req-nullable-removed</b> — NewPet.nickname no longer nullable (expected B: null rejected)</summary>

```diff
@@ -219,5 +219,4 @@
         nickname:
           type: string
-          nullable: true
         weight:
           type: integer
```
</details>
<details><summary><b>req-nullable-added</b> — NewPet.tag becomes nullable (expected N: accepts more)</summary>

```diff
@@ -210,4 +210,5 @@
         tag:
           type: string
+          nullable: true
         age:
           type: integer
```
</details>
<details><summary><b>req-maxitems-decreased</b> — NewPet.tags maxItems 10 → 3 (expected B: 4+ tags rejected)</summary>

```diff
@@ -224,5 +224,5 @@
         tags:
           type: array
-          maxItems: 10
+          maxItems: 3
           items:
             type: string
```
</details>
<details><summary><b>req-uniqueitems-set</b> — NewPet.tags gains uniqueItems: true (expected B: duplicates rejected)</summary>

```diff
@@ -227,4 +227,5 @@
           items:
             type: string
+          uniqueItems: true
         code:
           type: string
```
</details>
<details><summary><b>req-items-type-changed</b> — NewPet.tags items string → integer (expected B: string tags rejected)</summary>

```diff
@@ -226,5 +226,5 @@
           maxItems: 10
           items:
-            type: string
+            type: integer
         code:
           type: string
```
</details>
<details><summary><b>req-additionalprops-false</b> — NewPet gains additionalProperties: false (expected B: a client sending any extra field (e.g. one it reads back from Pet) is rejected)</summary>

```diff
@@ -232,4 +232,5 @@
           type: string
           default: none
+      additionalProperties: false
     Card:
       type: object
```
</details>
<details><summary><b>req-default-changed</b> — NewPet.notes default 'none' → '' (expected ?: wire-valid both ways, but clients that omit the field get different behaviour)</summary>

```diff
@@ -231,5 +231,5 @@
         notes:
           type: string
-          default: none
+          default: ''
     Card:
       type: object
```
</details>
<details><summary><b>req-prop-became-readonly</b> — NewPet.tag becomes readOnly (expected ?: server now ignores what the client sends: silent data loss, no error)</summary>

```diff
@@ -210,4 +210,5 @@
         tag:
           type: string
+          readOnly: true
         age:
           type: integer
```
</details>
<details><summary><b>req-required-prop-readonly</b> — NewPet.name (required) becomes readOnly (expected ?: same as above for a required field)</summary>

```diff
@@ -203,4 +203,5 @@
           minLength: 1
           maxLength: 50
+          readOnly: true
         status:
           type: string
```
</details>
<details><summary><b>req-allof-added</b> — NewPet wrapped in allOf with a required `species` (expected B: an extra required field via composition)</summary>

```diff
@@ -195,41 +195,48 @@
           type: string
     NewPet:
-      type: object
-      required:
-      - name
-      properties:
-        name:
-          type: string
-          minLength: 1
-          maxLength: 50
-        status:
-          type: string
-          enum:
-          - available
-          - sold
-        tag:
-          type: string
-        age:
-          type: integer
-          minimum: 0
-          maximum: 30
-        born:
-          type: string
-          format: date
-        nickname:
-          type: string
-          nullable: true
-        weight:
-          type: integer
-        tags:
-          type: array
-          maxItems: 10
-          items:
-            type: string
-        code:
-          type: string
-        notes:
-          type: string
-          default: none
+      allOf:
+      - type: object
+        required:
+        - name
+        properties:
+          name:
+            type: string
+            minLength: 1
+            maxLength: 50
+          status:
+            type: string
+            enum:
+            - available
+            - sold
+          tag:
+            type: string
+          age:
+            type: integer
+            minimum: 0
+            maximum: 30
+          born:
+            type: string
+            format: date
+          nickname:
+            type: string
+            nullable: true
+          weight:
+            type: integer
+          tags:
+            type: array
+            maxItems: 10
+            items:
+              type: string
+          code:
+            type: string
+          notes:
+            type: string
+            default: none
+      - type: object
+        required:
+        - species
+        properties:
+          species:
+            type: string
     Card:
       type: object
```
</details>
<details><summary><b>req-oneof-removed</b> — PaymentIn oneOf loses Cash (expected B: cash payments rejected)</summary>

```diff
@@ -265,10 +265,8 @@
       oneOf:
       - $ref: '#/components/schemas/Card'
-      - $ref: '#/components/schemas/Cash'
       discriminator:
         propertyName: kind
         mapping:
           card: '#/components/schemas/Card'
-          cash: '#/components/schemas/Cash'
     PaymentOut:
       oneOf:
```
</details>
<details><summary><b>req-oneof-added</b> — PaymentIn oneOf gains Voucher (expected N: accepts more)</summary>

```diff
@@ -266,4 +266,5 @@
       - $ref: '#/components/schemas/Card'
       - $ref: '#/components/schemas/Cash'
+      - $ref: '#/components/schemas/Voucher'
       discriminator:
         propertyName: kind
@@ -271,4 +272,5 @@
           card: '#/components/schemas/Card'
           cash: '#/components/schemas/Cash'
+          voucher: '#/components/schemas/Voucher'
     PaymentOut:
       oneOf:
```
</details>
<details><summary><b>req-discriminator-renamed</b> — PaymentIn discriminator propertyName kind → type (expected B: clients still send `kind`; the server dispatches on `type`)</summary>

```diff
@@ -267,5 +267,5 @@
       - $ref: '#/components/schemas/Cash'
       discriminator:
-        propertyName: kind
+        propertyName: type
         mapping:
           card: '#/components/schemas/Card'
```
</details>
<details><summary><b>req-discriminator-mapping-changed</b> — PaymentIn mapping value `card` → `CARD` (expected B: clients sending kind=card no longer match a branch)</summary>

```diff
@@ -269,6 +269,6 @@
         propertyName: kind
         mapping:
-          card: '#/components/schemas/Card'
           cash: '#/components/schemas/Cash'
+          CARD: '#/components/schemas/Card'
     PaymentOut:
       oneOf:
```
</details>
<details><summary><b>resp-required-prop-removed</b> — Pet.status (required) removed (expected B: clients read it)</summary>

```diff
@@ -157,5 +157,4 @@
       - id
       - name
-      - status
       properties:
         id:
@@ -165,9 +164,4 @@
           type: string
           maxLength: 50
-        status:
-          type: string
-          enum:
-          - available
-          - sold
         tag:
           type: string
```
</details>
<details><summary><b>resp-optional-prop-removed</b> — Pet.tag (optional) removed (expected ?: it was optional so clients must cope with absence; but a client that always got it breaks)</summary>

```diff
@@ -170,6 +170,4 @@
           - available
           - sold
-        tag:
-          type: string
         age:
           type: integer
```
</details>
<details><summary><b>resp-prop-became-optional</b> — Pet.name no longer required (expected B: clients may get no name)</summary>

```diff
@@ -156,5 +156,4 @@
       required:
       - id
-      - name
       - status
       properties:
```
</details>
<details><summary><b>resp-prop-became-required</b> — Pet.tag becomes required (expected N: a stronger guarantee)</summary>

```diff
@@ -158,4 +158,5 @@
       - name
       - status
+      - tag
       properties:
         id:
```
</details>
<details><summary><b>resp-optional-prop-added</b> — Pet gains optional `color` (expected N: tolerant readers ignore it)</summary>

```diff
@@ -185,4 +185,6 @@
         owner:
           $ref: '#/components/schemas/Owner'
+        color:
+          type: string
     Owner:
       type: object
```
</details>
<details><summary><b>resp-required-prop-added</b> — Pet gains required `color` (expected N: more data, still tolerant)</summary>

```diff
@@ -158,4 +158,5 @@
       - name
       - status
+      - color
       properties:
         id:
@@ -185,4 +186,6 @@
         owner:
           $ref: '#/components/schemas/Owner'
+        color:
+          type: string
     Owner:
       type: object
```
</details>
<details><summary><b>resp-type-changed</b> — Pet.age integer → string (expected B: deserialisation fails)</summary>

```diff
@@ -173,7 +173,5 @@
           type: string
         age:
-          type: integer
-          minimum: 0
-          maximum: 30
+          type: string
         born:
           type: string
```
</details>
<details><summary><b>resp-type-widened</b> — Pet.age integer → number (expected B: an int field receives 2.5)</summary>

```diff
@@ -173,5 +173,5 @@
           type: string
         age:
-          type: integer
+          type: number
           minimum: 0
           maximum: 30
```
</details>
<details><summary><b>resp-format-widened</b> — Pet.id format int64 → none (unbounded integer) (expected ?: format is advisory; a codegen client may pick a narrower type)</summary>

```diff
@@ -161,5 +161,4 @@
         id:
           type: integer
-          format: int64
         name:
           type: string
```
</details>
<details><summary><b>resp-format-changed</b> — Pet.born format date → date-time (expected B: a date parser fails on a timestamp)</summary>

```diff
@@ -178,5 +178,5 @@
         born:
           type: string
-          format: date
+          format: date-time
         tags:
           type: array
```
</details>
<details><summary><b>resp-maxlength-increased</b> — Pet.name maxLength 50 → 100 (expected B: a client that sized a column/buffer at 50 truncates or fails)</summary>

```diff
@@ -164,5 +164,5 @@
         name:
           type: string
-          maxLength: 50
+          maxLength: 100
         status:
           type: string
```
</details>
<details><summary><b>resp-maxlength-decreased</b> — Pet.name maxLength 50 → 20 (expected N: returns less)</summary>

```diff
@@ -164,5 +164,5 @@
         name:
           type: string
-          maxLength: 50
+          maxLength: 20
         status:
           type: string
```
</details>
<details><summary><b>resp-maximum-increased</b> — Pet.age maximum 30 → 99 (expected B: a client validating 0..30 rejects 50)</summary>

```diff
@@ -175,5 +175,5 @@
           type: integer
           minimum: 0
-          maximum: 30
+          maximum: 99
         born:
           type: string
```
</details>
<details><summary><b>resp-minimum-decreased</b> — Pet.age minimum 0 → -1 (expected B: negative ages appear)</summary>

```diff
@@ -174,5 +174,5 @@
         age:
           type: integer
-          minimum: 0
+          minimum: -1
           maximum: 30
         born:
```
</details>
<details><summary><b>resp-minimum-increased</b> — Pet.age minimum 0 → 1 (expected N: returns less)</summary>

```diff
@@ -174,5 +174,5 @@
         age:
           type: integer
-          minimum: 0
+          minimum: 1
           maximum: 30
         born:
```
</details>
<details><summary><b>resp-enum-value-added</b> — Pet.status enum gains `pending` (expected B: an exhaustive switch / generated enum fails on the new value)</summary>

```diff
@@ -170,4 +170,5 @@
           - available
           - sold
+          - pending
         tag:
           type: string
```
</details>
<details><summary><b>resp-enum-value-removed</b> — Pet.status enum loses `sold` (expected N: returns a subset)</summary>

```diff
@@ -169,5 +169,4 @@
           enum:
           - available
-          - sold
         tag:
           type: string
```
</details>
<details><summary><b>resp-enum-removed</b> — Pet.status enum constraint dropped (any string) (expected B: same as adding unknown values)</summary>

```diff
@@ -167,7 +167,4 @@
         status:
           type: string
-          enum:
-          - available
-          - sold
         tag:
           type: string
```
</details>
<details><summary><b>resp-nullable-added</b> — Pet.name becomes nullable (expected B: clients dereference null)</summary>

```diff
@@ -165,4 +165,5 @@
           type: string
           maxLength: 50
+          nullable: true
         status:
           type: string
```
</details>
<details><summary><b>resp-items-type-changed</b> — Pet.tags items string → integer (expected B: deserialisation fails)</summary>

```diff
@@ -182,5 +182,5 @@
           type: array
           items:
-            type: string
+            type: integer
         owner:
           $ref: '#/components/schemas/Owner'
```
</details>
<details><summary><b>resp-required-became-writeonly</b> — Pet.name (required) becomes writeOnly (expected B: writeOnly properties are never returned: a required response field disappears)</summary>

```diff
@@ -165,4 +165,5 @@
           type: string
           maxLength: 50
+          writeOnly: true
         status:
           type: string
```
</details>
<details><summary><b>resp-nested-ref-prop-removed</b> — Owner.ownerId (required, reached via Pet.owner) removed (expected B: same as a removed required response property, one $ref deeper)</summary>

```diff
@@ -187,9 +187,6 @@
     Owner:
       type: object
-      required:
-      - ownerId
-      properties:
-        ownerId:
-          type: integer
+      required: []
+      properties:
         email:
           type: string
```
</details>
<details><summary><b>resp-oneof-added</b> — PaymentOut oneOf gains Voucher (expected B: clients get a variant they cannot parse)</summary>

```diff
@@ -275,4 +275,5 @@
       - $ref: '#/components/schemas/Card'
       - $ref: '#/components/schemas/Cash'
+      - $ref: '#/components/schemas/Voucher'
       discriminator:
         propertyName: kind
@@ -280,4 +281,5 @@
           card: '#/components/schemas/Card'
           cash: '#/components/schemas/Cash'
+          voucher: '#/components/schemas/Voucher'
     Unused:
       type: object
```
</details>
<details><summary><b>resp-oneof-removed</b> — PaymentOut oneOf loses Cash (expected N: returns a subset)</summary>

```diff
@@ -274,10 +274,8 @@
       oneOf:
       - $ref: '#/components/schemas/Card'
-      - $ref: '#/components/schemas/Cash'
       discriminator:
         propertyName: kind
         mapping:
           card: '#/components/schemas/Card'
-          cash: '#/components/schemas/Cash'
     Unused:
       type: object
```
</details>
<details><summary><b>resp-discriminator-renamed</b> — PaymentOut discriminator propertyName kind → type (expected B: clients dispatch on `kind`, which no longer selects the subtype)</summary>

```diff
@@ -276,5 +276,5 @@
       - $ref: '#/components/schemas/Cash'
       discriminator:
-        propertyName: kind
+        propertyName: type
         mapping:
           card: '#/components/schemas/Card'
```
</details>
<details><summary><b>resp-discriminator-mapping-changed</b> — PaymentOut mapping value `card` → `CARD` (expected B: clients receive kind=CARD and match no subtype)</summary>

```diff
@@ -278,6 +278,6 @@
         propertyName: kind
         mapping:
-          card: '#/components/schemas/Card'
           cash: '#/components/schemas/Cash'
+          CARD: '#/components/schemas/Card'
     Unused:
       type: object
```
</details>
<details><summary><b>resp-header-removed</b> — 201 loses required Location header (expected B: clients read it)</summary>

```diff
@@ -62,8 +62,4 @@
           description: created
           headers:
-            Location:
-              required: true
-              schema:
-                type: string
             X-Rate:
               schema:
```
</details>
<details><summary><b>resp-header-optional-removed</b> — 201 loses optional X-Rate header (expected N: was optional)</summary>

```diff
@@ -66,7 +66,4 @@
               schema:
                 type: string
-            X-Rate:
-              schema:
-                type: integer
           content:
             application/json:
```
</details>
<details><summary><b>resp-header-type-changed</b> — 201 X-Rate integer → string (expected B: clients parse an int)</summary>

```diff
@@ -68,5 +68,5 @@
             X-Rate:
               schema:
-                type: integer
+                type: string
           content:
             application/json:
```
</details>
<details><summary><b>schema-renamed</b> — components.schemas.Owner renamed to Person (same shape) (expected N: the JSON on the wire is identical; only the component name moved)</summary>

```diff
@@ -184,14 +184,5 @@
             type: string
         owner:
-          $ref: '#/components/schemas/Owner'
-    Owner:
-      type: object
-      required:
-      - ownerId
-      properties:
-        ownerId:
-          type: integer
-        email:
-          type: string
+          $ref: '#/components/schemas/Person'
     NewPet:
       type: object
@@ -285,2 +276,11 @@
         x:
           type: string
+    Person:
+      type: object
+      required:
+      - ownerId
+      properties:
+        ownerId:
+          type: integer
+        email:
+          type: string
```
</details>
<details><summary><b>ref-inlined</b> — Pet.owner $ref replaced by the identical inline schema (expected N: no wire change)</summary>

```diff
@@ -184,5 +184,12 @@
             type: string
         owner:
-          $ref: '#/components/schemas/Owner'
+          type: object
+          required:
+          - ownerId
+          properties:
+            ownerId:
+              type: integer
+            email:
+              type: string
     Owner:
       type: object
```
</details>
<details><summary><b>unused-schema-removed</b> — components.schemas.Unused (referenced nowhere) removed (expected N: no operation sends or returns it)</summary>

```diff
@@ -280,7 +280,2 @@
           card: '#/components/schemas/Card'
           cash: '#/components/schemas/Cash'
-    Unused:
-      type: object
-      properties:
-        x:
-          type: string
```
</details>
<details><summary><b>unused-schema-changed</b> — components.schemas.Unused.x string → integer (expected N: no operation sends or returns it)</summary>

```diff
@@ -284,3 +284,3 @@
       properties:
         x:
-          type: string
+          type: integer
```
</details>
<details><summary><b>description-changed</b> — Pet.name gains a description (expected N: docs only)</summary>

```diff
@@ -165,4 +165,5 @@
           type: string
           maxLength: 50
+          description: the pet's name
         status:
           type: string
```
</details>
<details><summary><b>query-required-added</b> — GET /pets gains required query `owner` (expected B: old calls lack it)</summary>

```diff
@@ -33,4 +33,9 @@
         in: header
         required: false
+        schema:
+          type: string
+      - name: owner
+        in: query
+        required: true
         schema:
           type: string
```
</details>
<details><summary><b>query-optional-added</b> — GET /pets gains optional query `owner` (expected N: old calls still valid)</summary>

```diff
@@ -33,4 +33,8 @@
         in: header
         required: false
+        schema:
+          type: string
+      - name: owner
+        in: query
         schema:
           type: string
```
</details>
<details><summary><b>query-became-required</b> — GET /pets `limit` becomes required (expected B: calls without it rejected)</summary>

```diff
@@ -10,5 +10,5 @@
       - name: limit
         in: query
-        required: false
+        required: true
         schema:
           type: integer
```
</details>
<details><summary><b>query-removed</b> — GET /pets drops `status` (expected ?: server ignores the unknown param: no error, but the filter silently stops applying)</summary>

```diff
@@ -15,11 +15,4 @@
           minimum: 1
           maximum: 100
-      - name: status
-        in: query
-        schema:
-          type: string
-          enum:
-          - available
-          - sold
       - name: ids
         in: query
```
</details>
<details><summary><b>query-type-changed</b> — GET /pets `limit` integer → boolean (expected B: limit=10 rejected)</summary>

```diff
@@ -12,7 +12,5 @@
         required: false
         schema:
-          type: integer
-          minimum: 1
-          maximum: 100
+          type: boolean
       - name: status
         in: query
```
</details>
<details><summary><b>query-max-decreased</b> — GET /pets `limit` maximum 100 → 50 (expected B: limit=80 rejected)</summary>

```diff
@@ -14,5 +14,5 @@
           type: integer
           minimum: 1
-          maximum: 100
+          maximum: 50
       - name: status
         in: query
```
</details>
<details><summary><b>query-enum-value-removed</b> — GET /pets `status` enum loses `sold` (expected B: status=sold rejected)</summary>

```diff
@@ -21,5 +21,4 @@
           enum:
           - available
-          - sold
       - name: ids
         in: query
```
</details>
<details><summary><b>query-explode-changed</b> — GET /pets `ids` explode true → false (expected B: wire format changes from ids=1&ids=2 to ids=1,2; old calls are misparsed)</summary>

```diff
@@ -25,5 +25,5 @@
         in: query
         style: form
-        explode: true
+        explode: false
         schema:
           type: array
```
</details>
<details><summary><b>query-style-changed</b> — GET /pets `ids` style form → pipeDelimited (expected B: wire format changes from ids=1&ids=2 to ids=1|2)</summary>

```diff
@@ -24,6 +24,6 @@
       - name: ids
         in: query
-        style: form
-        explode: true
+        style: pipeDelimited
+        explode: false
         schema:
           type: array
```
</details>
<details><summary><b>header-required-added</b> — GET /pets gains required header X-Tenant (expected B: old calls lack it)</summary>

```diff
@@ -33,4 +33,9 @@
         in: header
         required: false
+        schema:
+          type: string
+      - name: X-Tenant
+        in: header
+        required: true
         schema:
           type: string
```
</details>
<details><summary><b>header-became-required</b> — GET /pets header X-Trace becomes required (expected B: old calls lack it)</summary>

```diff
@@ -32,5 +32,5 @@
       - name: X-Trace
         in: header
-        required: false
+        required: true
         schema:
           type: string
```
</details>
<details><summary><b>cookie-required-added</b> — GET /pets gains required cookie `session` (expected B: old calls lack it)</summary>

```diff
@@ -33,4 +33,9 @@
         in: header
         required: false
+        schema:
+          type: string
+      - name: session
+        in: cookie
+        required: true
         schema:
           type: string
```
</details>
<details><summary><b>path-param-type-narrowed</b> — GET /payments/{pid} pid string → integer (expected B: pid=abc rejected)</summary>

```diff
@@ -129,5 +129,5 @@
         required: true
         schema:
-          type: string
+          type: integer
       responses:
         '200':
```
</details>
<details><summary><b>path-level-param-required-added</b> — path-level required query `tenant` on /pets/{id} (expected B: applies to GET and DELETE; old calls lack it)</summary>

```diff
@@ -109,4 +109,10 @@
         '204':
           description: gone
+    parameters:
+    - name: tenant
+      in: query
+      required: true
+      schema:
+        type: string
   /payments:
     post:
```
</details>
<details><summary><b>path-level-param-became-required</b> — path-level optional `tenant` becomes required (expected B: old calls lack it) _(base differs from the common one)_</summary>

```diff
@@ -112,5 +112,5 @@
     - name: tenant
       in: query
-      required: false
+      required: true
       schema:
         type: string
```
</details>
<details><summary><b>component-param-became-required</b> — components.parameters.Limit (via $ref) becomes required (expected B: old calls lack it) _(base differs from the common one)_</summary>

```diff
@@ -283,5 +283,5 @@
       name: limit
       in: query
-      required: false
+      required: true
       schema:
         type: integer
```
</details>
<details><summary><b>op-security-added</b> — GET /pets/{id} (anonymous) now requires apiKey (expected B: anonymous callers get 401)</summary>

```diff
@@ -97,4 +97,6 @@
         '404':
           description: not found
+      security:
+      - apiKey: []
     delete:
       operationId: deletePet
```
</details>
<details><summary><b>global-security-added</b> — top-level security: apiKey added (ops had none) (expected B: every anonymous caller gets 401)</summary>

```diff
@@ -285,2 +285,4 @@
         x:
           type: string
+security:
+- apiKey: []
```
</details>
<details><summary><b>security-scope-added</b> — POST /pets needs pets:admin besides pets:write (expected B: existing tokens lack it)</summary>

```diff
@@ -49,4 +49,5 @@
       - oauth:
         - pets:write
+        - pets:admin
       requestBody:
         required: true
```
</details>
<details><summary><b>security-scheme-removed</b> — POST /pets security requirement removed (expected N: accepts more)</summary>

```diff
@@ -46,7 +46,4 @@
     post:
       operationId: createPet
-      security:
-      - oauth:
-        - pets:write
       requestBody:
         required: true
```
</details>
<details><summary><b>apikey-header-renamed</b> — apiKey scheme header X-API-Key → X-Token (used by GET /pets) (expected B: clients send the key in the old header and get 401) _(base differs from the common one)_</summary>

```diff
@@ -144,5 +144,5 @@
       type: apiKey
       in: header
-      name: X-API-Key
+      name: X-Token
     oauth:
       type: oauth2
```
</details>
<details><summary><b>security-scheme-type-changed</b> — apiKey scheme replaced by http bearer (same name, used by GET /pets) (expected B: clients send an API key header; server expects Authorization: Bearer) _(base differs from the common one)_</summary>

```diff
@@ -142,7 +142,6 @@
   securitySchemes:
     apiKey:
-      type: apiKey
-      in: header
-      name: X-API-Key
+      type: http
+      scheme: bearer
     oauth:
       type: oauth2
```
</details>
<details><summary><b>oauth-token-url-changed</b> — oauth tokenUrl moved (expected ?: clients fetch tokens from the old URL)</summary>

```diff
@@ -147,5 +147,5 @@
       flows:
         clientCredentials:
-          tokenUrl: https://auth.example.com/token
+          tokenUrl: https://auth2.example.com/token
           scopes:
             pets:write: write
```
</details>
<details><summary><b>server-basepath-changed</b> — servers url /v1 → /v2 (expected ?: every URL moves for a client that builds them from the spec; oasdiff calls servers deployment metadata) _(base differs from the common one)_</summary>

```diff
@@ -286,3 +286,3 @@
           type: string
 servers:
-- url: https://api.example.com/v1
+- url: https://api.example.com/v2
```
</details>
<details><summary><b>resp-header-became-optional</b> — 201 Location header no longer required (expected B: clients read it unconditionally)</summary>

```diff
@@ -63,5 +63,5 @@
           headers:
             Location:
-              required: true
+              required: false
               schema:
                 type: string
```
</details>
<details><summary><b>req-multipleof-set</b> — NewPet.weight gains multipleOf: 5 (expected B: weight 7 rejected)</summary>

```diff
@@ -222,4 +222,5 @@
         weight:
           type: integer
+          multipleOf: 5
         tags:
           type: array
```
</details>
<details><summary><b>req-minitems-set</b> — NewPet.tags gains minItems: 1 (expected B: empty list rejected)</summary>

```diff
@@ -227,4 +227,5 @@
           items:
             type: string
+          minItems: 1
         code:
           type: string
```
</details>
<details><summary><b>resp-maxitems-set-then-raised</b> — Pet.tags gains maxItems 5 (response narrowing) (expected N: returns less)</summary>

```diff
@@ -183,4 +183,5 @@
           items:
             type: string
+          maxItems: 5
         owner:
           $ref: '#/components/schemas/Owner'
```
</details>
<details><summary><b>resp-body-type-changed</b> — GET /pets returns an object page instead of an array (expected B: deserialisation fails)</summary>

```diff
@@ -41,7 +41,10 @@
             application/json:
               schema:
-                type: array
-                items:
-                  $ref: '#/components/schemas/Pet'
+                type: object
+                properties:
+                  items:
+                    type: array
+                    items:
+                      $ref: '#/components/schemas/Pet'
     post:
       operationId: createPet
```
</details>
<details><summary><b>req-body-schema-swapped</b> — POST /pets body NewPet → Pet (requires id, status) (expected B: old payloads lack id/status)</summary>

```diff
@@ -54,8 +54,8 @@
           application/json:
             schema:
-              $ref: '#/components/schemas/NewPet'
+              $ref: '#/components/schemas/Pet'
           application/xml:
             schema:
-              $ref: '#/components/schemas/NewPet'
+              $ref: '#/components/schemas/Pet'
       responses:
         '201':
```
</details>
<details><summary><b>resp-media-renamed</b> — GET /pets/{id} application/json → application/vnd.pet+json (expected B: Accept: application/json now gets 406)</summary>

```diff
@@ -89,8 +89,8 @@
           description: ok
           content:
-            application/json:
+            application/xml:
               schema:
                 $ref: '#/components/schemas/Pet'
-            application/xml:
+            application/vnd.pet+json:
               schema:
                 $ref: '#/components/schemas/Pet'
```
</details>
<details><summary><b>resp-anyof-added</b> — Pet.tag string → anyOf [string, integer] (expected B: clients get integers in a string field)</summary>

```diff
@@ -171,5 +171,7 @@
           - sold
         tag:
-          type: string
+          anyOf:
+          - type: string
+          - type: integer
         age:
           type: integer
```
</details>
<details><summary><b>req-anyof-removed</b> — NewPet.weight anyOf [integer, string] → anyOf [integer] (expected B: string weights rejected) _(base differs from the common one)_</summary>

```diff
@@ -223,5 +223,4 @@
           anyOf:
           - type: integer
-          - type: string
         tags:
           type: array
```
</details>
<details><summary><b>resp-allof-part-removed</b> — Pet = allOf [Base, Extra] loses Extra (required `status`) (expected B: a required response field disappears) _(base differs from the common one)_</summary>

```diff
@@ -155,5 +155,4 @@
       allOf:
       - $ref: '#/components/schemas/PetBase'
-      - $ref: '#/components/schemas/PetExtra'
     Owner:
       type: object
```
</details>
<details><summary><b>resp-required-became-readonly</b> — Pet.name (required) becomes readOnly (expected N: readOnly fields are still returned)</summary>

```diff
@@ -165,4 +165,5 @@
           type: string
           maxLength: 50
+          readOnly: true
         status:
           type: string
```
</details>
<details><summary><b>oas31-resp-null-added</b> — 3.1: Pet.tag type string → [string, null] (expected B: clients dereference null) _(base differs from the common one)_</summary>

```diff
@@ -171,5 +171,7 @@
           - sold
         tag:
-          type: string
+          type:
+          - string
+          - 'null'
         age:
           type: integer
```
</details>
<details><summary><b>oas31-req-const-added</b> — 3.1: NewPet.status gains const: available (expected B: 'sold' rejected) _(base differs from the common one)_</summary>

```diff
@@ -208,4 +208,5 @@
           - available
           - sold
+          const: available
         tag:
           type: string
```
</details>
<details><summary><b>req-not-added</b> — NewPet.code gains not: {enum: [admin]} (expected B: 'admin' rejected)</summary>

```diff
@@ -229,4 +229,7 @@
         code:
           type: string
+          not:
+            enum:
+            - admin
         notes:
           type: string
```
</details>
<details><summary><b>resp-additionalprops-schema-widened</b> — Owner gains additionalProperties: true where it had false (expected B: clients with closed models (additionalProperties false) see unknown keys — only for strict readers) _(base differs from the common one)_</summary>

```diff
@@ -194,5 +194,5 @@
         email:
           type: string
-      additionalProperties: false
+      additionalProperties: true
     NewPet:
       type: object
```
</details>
<details><summary><b>query-required-with-default</b> — GET /pets gains required query `sort` with default (expected B: required means the client must send it; the default does not make old calls valid)</summary>

```diff
@@ -35,4 +35,10 @@
         schema:
           type: string
+      - name: sort
+        in: query
+        required: true
+        schema:
+          type: string
+          default: name
       responses:
         '200':
```
</details>
<details><summary><b>req-enum-removed</b> — NewPet.status enum constraint dropped (any string) (expected N: accepts more)</summary>

```diff
@@ -205,7 +205,4 @@
         status:
           type: string
-          enum:
-          - available
-          - sold
         tag:
           type: string
```
</details>

