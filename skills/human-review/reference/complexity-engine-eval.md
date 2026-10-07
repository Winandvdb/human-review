# The Complexity tab's second engine: JavaParser, and the eval it had to pass

*7 Oct 2026.* `endpoint-complexity.py` measured every entry point with regular expressions
over blanked Java source. It needs nothing but Python, and it is wrong in ways nobody can see:
a call it cannot place is dropped in silence, a name it cannot type is guessed by being the
only method of that name in the project, overloads collapse into one method, nested classes
are filed under their outer class, and nesting is counted by braces, so a brace-less `if`
nests nothing. This page is the design of the replacement and the evidence it was held to
before it became the default.

## Design

**One Java class, owned by the skill** — `scripts/complexity/ComplexityEngine.java`. It uses
[JavaParser](https://javaparser.org) **3.28.2** and its **symbol solver** (latest on Maven
Central on 7 Oct 2026, released 31 May 2026), language level Java 25.

**How it gets onto the machine.** No Maven/Gradle module and no jar in the repository:

* five jars — `javaparser-core`, `javaparser-symbol-solver-core` (3.28.2), `javassist`
  3.31.0-GA, `guava` 33.6.0-jre, `failureaccess` 1.0.3 (the versions JavaParser's own parent
  POM pins) — are **pinned by sha256** in `endpoint-complexity.py` (`JARS`). Each is taken
  from `~/.cache/human-review/complexity-engine/lib/`, else from `~/.m2/repository` if the
  bytes match, else downloaded once from Maven Central and verified. The hashes were checked
  against Central's own `.sha1` when they were pinned. A jar that does not match is never put
  on a classpath;
* the one source file is compiled with `javac --release 17` into
  `~/.cache/human-review/complexity-engine/<hash>/`, keyed by the sha256 of the source and the
  jar hashes — an edit to the engine rebuilds it, nothing else does. Same bargain as the
  test-coverage tools (`testcov.py`): a binary in the repository is a binary nobody reviews,
  and the class compiles in about two seconds.

Why not a fat jar from a committed Maven module: it needs `mvn` on the reviewer's machine and
a build step to keep in sync; the single file + pinned jars needs only a JDK, which the engine
needs anyway to run.

**What it reads.** Only sources, never the build. The sources (working tree, or a revision read
out of git — same `sources()` the regex engine uses) are written into a scratch tree, and the
type solver is every `src/main/java` root in it (all modules) plus the JDK by reflection. No
library jar is on the solver, so a call into Spring, Jackson, Spring AI… resolves to nothing
and is dropped, exactly as before.

**Output.** The same JSON list as the regex engine (`endpoint-complexity-delta.py` and the tab
read it unchanged), plus: `engine` per entry point, `unresolvedCount` and `unresolved[]`
(`from`, `call`, `file`, `line`, `reason`), and `file`/`line` of every flow method's
declaration. An overloaded method's key carries its parameters (`pkg.C#render(int)`); a nested
class is named as such (`pkg.Outer.Inner#m`); enum constant bodies are types of their own
(`pkg.Op.MINUS#apply`).

**Scoring** — Cognitive Complexity (G. Ann Campbell / SonarSource), from the syntax tree:

* `+1 + nesting` for `if`, ternary, `switch` (statement or expression), `for`, for-each,
  `while`, `do`, `catch`; `+1` flat for `else`, `else if`, a labeled `break`/`continue`, and
  each run of like boolean operators — flattened through parentheses, broken by `!` and by a
  method call, as SonarJava does;
* nesting is raised by the bodies of those constructs, by lambdas, and by methods of
  anonymous and local classes — whose increments belong to the enclosing method (white
  paper: "nested methods");
* `+1` for **direct** recursion, charged once on the first call that closes the loop.
  Indirect cycles are not charged (the white paper would charge each method in a cycle;
  the regex engine never did, and the delta must compare like with like);
* the condition of an `if` is read at the `if`'s own level; loop headers, a ternary's
  operands and a switch's selector at the level inside them.

**Flow** — breadth-first over resolved calls from the handler; `flowCc` is the sum over the
DISTINCT methods reached. Calls are method calls, method references of all four kinds,
`new`, and `this(…)`/`super(…)`.

* A call binds by the symbol solver. A call on an interface, an abstract or any overridable
  method runs **every project override** — including an implementation a class only
  inherits (`class Impl extends BaseImpl implements Svc {}`) — and the declaration itself
  only if it has a body: static analysis cannot say which object arrives, so all of them are
  counted. An over-count, stated. `super.m()` binds to the parent's body alone.
* When the solver fails (usually an argument whose type lives in a library jar it does not
  have), the receiver's type is **read off the source** (`infer`): the declaration of the
  variable, field or parameter; the declared return type of the project method a chain goes
  through (a type variable takes the receiver's type argument — `NamedRepository<Product>
  .findByName` is an `Optional<Product>`); a Lombok getter's field type, `@With` and chained
  setters, builders. The call then binds by **name and arity** on that type and its project
  supertypes; every overload that fits is followed.
* A value of a library type can **carry** project types: its type arguments
  (`ResponseEntity<Owner>`), the first type argument of a library supertype
  (`JpaRepository<Owner, OwnerId>` hands back Owners, never ids), a class literal
  (`getForObject(url, Owner.class)`), the project values a library factory is handed
  (`Mono.just(order)`). A call on the library value itself is the library's and is dropped;
  a call on what comes out of it binds to a carried type — unless the name is one the JDK or
  a container answers to (`isEmpty`, `get`, `getContent`, `getBody`, `block`, …), which stays
  the container's, and unless two carried types declare it, which is **reported as
  ambiguous**, never guessed.
* An untyped lambda parameter is, in order: the parameter type of the project method the
  lambda is handed to, at that argument's position (`Consumer<PriceCalculator>`); the
  element of the value a one-parameter lambda is called on (`owners.stream().map(o -> …)`);
  the declared functional type it is assigned or returned as (`ItemProcessor<Order,
  Invoice>`). A library target with nothing of ours in it makes the parameters the library's
  (`Specification<T> s = (root, query, cb) -> …`). Anything else is unknown.
* Dropped without a report: a call whose receiver is declared with a library type; a library
  static import (`checkNotNull`); `@Slf4j`'s `log`; methods inherited from a library supertype
  (`JpaRepository.save`); Spring Data derived queries (abstract, no body in source); record
  accessors, `values()`/`valueOf()`; Lombok-generated accessors, builders and constructors; and
  a call with a JDK method name (`stream`, `equalsIgnoreCase`, …) on the unbound *result of
  another call* — never on a named receiver.
* **Reported** as "not followed" (`unresolved`): a call on a receiver none of the above can
  type, when the project declares a method of that name; an ambiguous carried type; a project
  type that does not declare the method and has no library supertype it could come from. The
  chip on the row is the honest remainder.
* The same class in two modules (`x.Util` in `before/` and `after/`, a copied utility class)
  is two classes: the second is named `x.Util[module]`, and a call goes to the copy in the
  caller's module.
* Not modelled, stated: field initializers and instance initializer blocks (never scored);
  a call through a library interface into a project implementation (an interface from a shared
  jar implemented here) — the solver binds it to the library and it is dropped; a
  generic base controller's handler inherited by two subclasses with their own class-level
  paths (one row, both bodies of an overridden hook mixed); a template method called on a
  concrete receiver counts every override of the hook, not the receiver's.

**Entry points** — as before: `@GetMapping`/`@PostMapping`/`@PutMapping`/`@DeleteMapping`/
`@PatchMapping`/`@RequestMapping` (verb from `method =`, `ANY` otherwise) joined to the
class-level mapping, `@McpTool`/`@Tool` (`name`), `@KafkaListener`/`@RabbitListener`/
`@JmsListener` (`topics`/`queues`/`destination`), `@Scheduled`. Improvements: a path given as a
constant (`@PostMapping(VisitBookedNotification.PATH)`) is folded to its value; a fully-qualified
annotation (`@org.springframework…GetMapping`) counts; a mapping declared on an interface — an
OpenAPI-generated `…Api`, even one whose methods are `default` stubs — starts the flow in the
controller that implements it, under that controller's class-level path. Two entry points with one
name (two `@KafkaListener(topics = "orders")`) are told apart by handler in the tab, decided over
*both* snapshots so an untouched one never churns into "gone" + "new" (`load_pair`).

**Fallback.** `endpoint-complexity.py --engine auto` (the default) runs JavaParser when `java`
and `javac` are on the PATH, the regex engine otherwise — and also when the jars cannot be
fetched or a source fails to parse (the engine refuses the whole snapshot rather than lose the
entry points in that file). `--engine regex|javaparser` or `HR_COMPLEXITY_ENGINE` forces one.
The tab's lede names the engine that produced the numbers, and says so when the merge-base and
the branch were measured by different ones. A row with calls not followed shows
"N not followed"; its hover lists each call, where it is, and why.

## Eval 1 — a corpus of tricky shapes, hand-scored

`scripts/testdata/complexity-corpus/` — 51 entry points, each exercising one shape, the
expected flow and score in `expected.json`, the arithmetic as a comment on every line that
costs. `python3 scripts/test_complexity_engines.py` prints this table;
`pytest scripts/test_complexity_engines.py` holds the JavaParser engine to all of it.

| case | shape | expected | regex | JavaParser |
|---|---|---|---|---|
| `GET /c01` | method ref, static (Type::static) | 1 | 1 · ok | 1 · ok |
| `GET /c02` | method ref, bound (field::method) | 3 | 3 · ok | 3 · ok |
| `GET /c03` | method ref, unbound (Type::instanceMethod) | 1 | 1 · ok | 1 · ok |
| `GET /c04` | method ref, constructor (Type::new) | 1 | 1 · ok | 1 · ok |
| `GET /c05` | lambda body nests | 2 | 2 · ok | 2 · ok |
| `GET /c06` | chained calls a().b().c(), a decoy with the same name | 2 | 0 · cc 0, flow | 2 · ok |
| `GET /c07` | overload picked by argument type (int vs String) | 1 | 4 · cc 4 | 1 · ok |
| `GET /c08` | overload, most specific (String over Object) | 2 | 3 · cc 3 | 2 · ok |
| `GET /c09` | generic interface field, chained call on T | 2 | 1 · cc 1, flow | 2 · ok |
| `GET /c10` | static nested class, same method name as outer | 1 | 2 · cc 2, flow | 1 · ok |
| `GET /c11` | anonymous class method folds into the handler, nested | 2 | 2 · flow | 2 · ok |
| `GET /c12` | local class method folds into the handler, nested | 2 | 2 · flow | 2 · ok |
| `GET /c13` | record: compact constructor, method, implicit accessor | 2 | 1 · cc 1, flow | 2 · ok |
| `GET /c14` | enum with constant-specific bodies (abstract method) | 1 | 1 · flow | 1 · ok |
| `GET /c15` | static + default interface methods, dispatch to the impl | 1 | 0 · cc 0, flow | 1 · ok |
| `GET /c16` | static import, a decoy with the same name | 3 | 0 · cc 0, flow | 3 · ok |
| `GET /c17` | override + super.method() | 2 | 1 · cc 1, flow | 2 · ok |
| `GET /c17b` | constructor chaining this(...) | 1 | 0 · cc 0, flow | 1 · ok |
| `GET /c18` | recursion +1; an overload calling another is not recursion | 2 | 3 · cc 3, flow | 2 · ok |
| `GET /c19` | brace-less if / for nesting | 6 | 4 · cc 4 | 6 · ok |
| `GET /c20` | brace-less else-if chain | 3 | 3 · ok | 3 · ok |
| `GET /c21` | switch expression with arrows, yield | 5 | 6 · cc 6 | 5 · ok |
| `GET /c22` | try-with-resources, catch, finally | 3 | 3 · ok | 3 · ok |
| `GET /c23` | nested ternary | 3 | 2 · cc 2 | 3 · ok |
| `GET /c24` | Spring Data repository calls (inherited + derived query), a decoy save() | 0 | 3 · cc 3, flow | 0 · ok |
| `GET /c25` | boolean operator sequences, ! breaks a run | 5 | 6 · cc 6 | 5 · ok |
| `GET /c26` | interface dispatch to every impl, not to a same-name stranger | 4 | 5 · cc 5, flow | 4 · ok |
| `GET /c27` | generic static method, brace-less for/if | 4 | 3 · cc 3 | 4 · ok |
| `GET /c28` | stream lambdas: && and a ternary inside a lambda | 3 | 2 · cc 2 | 3 · ok |
| `GET /c29` | labeled break | 7 | 6 · cc 6 | 7 · ok |
| `GET /c30` | varargs overload | 1 | 2 · cc 2 | 1 · ok |
| `GET /c32` | inherited method, no override | 1 | 1 · ok | 1 · ok |
| `GET /c33` | this::method | 1 | 1 · ok | 1 · ok |
| `GET /c34` | constructor overloads | 1 | 0 · cc 0, flow | 1 · ok |
| `GET /c35` | method ref to an overloaded method | 1 | 2 · cc 2 | 1 · ok |
| `GET /api/c37/x` | class-level @RequestMapping from a constant | 1 | — | 1 · ok |
| `DELETE /api/c37/y` | @RequestMapping(method = DELETE) | 0 | — | 0 · ok |
| `MCP c38_tool` | @McpTool(name=...) | 1 | 1 · ok | 1 · ok |
| `JOB C38OtherEntries.tick` | @Scheduled job | 1 | 1 · ok | 1 · ok |
| `KAFKA c38-topic` | @KafkaListener(topics=...) | 1 | 1 · ok | 1 · ok |
| `GET /c39` | do-while | 1 | 1 · ok | 1 · ok |
| `GET /c41` | method ref assigned to a Function | 1 | 1 · ok | 1 · ok |
| `GET /c42` | annotated parameters with nested annotations | 1 | 1 · ok | 1 · ok |
| `GET /c43` | keywords inside strings, comments, text blocks | 0 | 0 · ok | 0 · ok |
| `GET /c45` | receiver declared in a library superclass, project has the name: report, never guess | 0 | 1 · cc 1, flow, unresolved - | 0 · ok |
| `GET /c45b` | chain rooted at a library class with nothing of ours: dropped, not reported | 0 | 1 · cc 1, flow | 0 · ok |
| `GET /c46` | Outer.Inner.staticCall(), same name on Outer | 1 | 0 · cc 0, flow | 1 · ok |
| `GET /c49` | instanceof pattern && ... | 2 | 4 · cc 4, flow | 2 · ok |
| `GET /c50` | indirect recursion (no +1: direct only, stated) | 2 | 2 · ok | 2 · ok |
| `GET /c51` | switch pattern with a guard | 4 | 6 · cc 6, flow | 4 · ok |
| `GET /c52` | Lombok @Data accessors (no source): dropped, not reported | 1 | 1 · ok | 1 · ok |
| `GET /c53` | call on a type variable bounded by an interface | 4 | 0 · cc 0, flow | 4 · ok |
| `GET /a1` | [adversarial] implementation inherited from a superclass that does not implement the interface | 1 | 1 · ok | 1 · ok |
| `GET /a2` | [adversarial] var o = jpaRepo.findById(id).orElseThrow(); o.total() | 1 | 1 · ok | 1 · ok |
| `GET /a3` | [adversarial] jpaRepo.findById(id).orElseThrow().total() | 1 | 1 · ok | 1 · ok |
| `GET /a4` | [adversarial] Owner o = jpaRepo.findById(id).orElseThrow(); o.total() | 1 | 1 · ok | 1 · ok |
| `GET /a5` | [adversarial] jpaRepo.findAll().stream().map(Owner::total) | 1 | 1 · ok | 1 · ok |
| `GET /a6` | [adversarial] jpaRepo.findAll().stream().map(o -> o.total()) | 1 | 1 · ok | 1 · ok |
| `GET /s` | [adversarial] Lombok @Slf4j log.error(): a library call, a decoy error() in the project | 0 | 1 · cc 1, flow | 0 · ok |
| `GET /da` | [adversarial] the same class (x.Util) in two modules: module a's copy | 1 | 1 · ok | 1 · ok |
| `GET /db` | [adversarial] the same class (x.Util) in two modules: module b's copy | 3 | 1 · cc 1 | 3 · ok |
| `GET /e1` | [adversarial] chain through Lombok getters, a decoy getId() elsewhere | 0 | 0 · flow | 0 · ok |
| `GET /f1` | [adversarial] OpenAPI interface with a default stub: the controller runs | 3 | 1 · cc 1, flow | 3 · ok |
| `GET /api/owners` | [adversarial] mapping on an interface, class-level path on the controller | 1 | — | 1 · ok |
| `GET /f4` | [adversarial] rest.getForObject(url, Owner.class).score() | 1 | 0 · cc 0, flow | 1 · ok |
| `GET /f5` | [adversarial] ResponseEntity<Owner>.getBody().score() | 1 | 0 · cc 0, flow | 1 · ok |
| `GET /g1` | [adversarial] locals and fields of library types, decoy names in the project | 0 | 0 · ok | 0 · ok |
| `GET /g2` | [adversarial] new Req() where Lombok writes the no-arg constructor | 0 | 0 · flow | 0 · ok |
| `GET /fq` | [adversarial] fully-qualified @org.springframework…GetMapping | 1 | — | 1 · ok |
| `JOB C.job` | [adversarial] fully-qualified @Scheduled | 0 | — | 0 · ok |
| `GET /p1` | [adversarial 2] Page<Post>.getContent() is the library's, not Post.getContent | 0 | 1 · cc 1, flow | 0 · ok |
| `GET /p2` | [adversarial 2] List<Post>.isEmpty() is the library's, not Post.isEmpty | 0 | 2 · cc 2, flow | 0 · ok |
| `GET /p3` | [adversarial 2] ResponseEntity<Map<Post,Vet>>.getBody().get(k).check(): truth 3 (Vet); two carried types declare check, so it is reported, not guessed | 0 | 0 · unresolved - | 0 · ok |
| `GET /p4` | [adversarial 2] mp.zipWith(mv, (p, v) -> v.check()): truth 3; a two-parameter lambda on a library call is reported, not guessed | 0 | 0 · unresolved - | 0 · ok |
| `GET /p5` | [adversarial 2] Mono.just(post).map(x -> x.check()) | 1 | 0 · cc 0, flow | 1 · ok |
| `GET /p6` | [adversarial 2] repo.findById(id).get().check() | 1 | 0 · cc 0, flow | 1 · ok |
| `GET /d1` | [adversarial 2] Mono.just(order).map(x -> x.score()) | 1 | 0 · cc 0, flow | 1 · ok |
| `GET /d2` | [adversarial 2] Flux.fromIterable(orders).map(o -> o.score()) | 1 | 0 · cc 0, flow | 1 · ok |
| `GET /d3` | [adversarial 2] ItemProcessor<Order, Invoice> p = o -> o.toInvoice() | 3 | 2 · cc 2 | 3 · ok |
| `GET /d4` | [adversarial 2] withRetry(libraryArg, calc -> calc.apply(o)) with a Consumer<PriceCalculator> parameter | 1 | 0 · cc 0, flow | 1 · ok |
| `GET /i1` | [adversarial 2] JpaRepository<Owner, OwnerId>: findById(...).orElseThrow() is an Owner, never the id | 1 | 0 · cc 0, flow | 1 · ok |
| `GET /i2` | [adversarial 2] getReferenceById(id) is an Owner | 1 | 0 · cc 0, flow | 1 · ok |
| `GET /i3` | [adversarial 2] findAll().stream().allMatch(o -> o.isValid()) | 1 | 0 · cc 0, flow | 1 · ok |
| `GET /t1` | [adversarial 2] import static of a class duplicated across modules: the caller's module's copy | 1 | 0 · cc 0, flow | 1 · ok |

84 cases — regex exact on 26, JavaParser exact on 84.
Entry points not in the expectations — regex: ['DELETE /y', 'GET /x'], JavaParser: []

Where they part, in short: the regex engine merges overloads (`C07`, `C08`, `C18`, `C30`, `C35`), files
nested classes under the outer one (`C10`, `C46`), guesses an untyped receiver by the only method of that
name (`C24` binds a Spring Data `save` to an unrelated `C24Audit.save`, `C26` reaches a non-implementing
`C26Mailer.send`), loses chained calls, static imports, constructors and `super`/`this(…)` (`C06`, `C16`,
`C17`, `C17b`, `C34`), counts nesting by braces (`C19`, `C21`, `C23`, `C28`), ignores labeled jumps
(`C29`), reads a `!` as part of a boolean run (`C25`) and cannot fold a constant path (`C37`). The
JavaParser engine scores every case exactly; the cases tagged `[adversarial]` were added from Eval 3,
after the fixes it forced.

## Eval 2 — real code

Both engines on `~/workspace/petclinic` (a read-only clone of branch `Devoxx26`, tip `d01c3776`, and
its merge-base with `origin/main`, `fe553439`) and on the workbench
`~/workspace/petclinic-pr-owner-grid-paginated` (`hr-claude-18`, same merge-base): 54 rows, 47
identical in both engines on both sides. The seven that differ, merge-base → tip:

| entry point | regex | JavaParser | who is right, read off the source |
|---|---|---|---|
| `POST /` vs `POST /api/notifications/visit-booked` | `POST /`, 4 | `…/visit-booked`, 1 | JavaParser: the path is `@PostMapping(VisitBookedNotification.PATH)`, a constant; regex reads no string and files it under `/`. The 4 is `PhoneNumbers.normalize` overloads merged (1 + 2) plus a phantom recursion (+1: one overload calling the other) |
| `POST /api/owners/{ownerId}/pets` | 3 → 3 | 1 → 1 | JavaParser: `petMapper.toPet(PetFieldsDto)` never calls `toVisits`; regex merged it with `toPet(PetDto)` |
| `POST /api/owners/{ownerId}/pets/{petId}/visits` | 5 → 9 (+4) on petclinic, 5 → 5 on the workbench | 4 → 8 (+4), 4 → 4 | JavaParser: regex adds the false `normalize` recursion, and reaches `NotificationController.visitBooked` in *another service* through the backend's `NotificationSender` interface (any class with that method name); JavaParser dispatches to the one implementation, `NotificationServiceClient` |
| `POST /api/specialties` | 3 | 0 | JavaParser: `toSpecialty(SpecialtyDto)` is straight-line; the 3 is the `toSpecialty(List)` overload |
| `POST /api/vets`, `PUT /api/vets/{vetId}` | 4, 5 | 3, 4 | JavaParser: the same `toSpecialty` overload merge |

The deltas the tab draws (`+4` on the visits POST in petclinic, `+1` on `GET /api/owners` in the
workbench) agree in both engines; the absolute numbers are the ones regex inflates. Flows also
differ in size where no score does: JavaParser follows fluent setters (`new OwnerDto().setId(…)
.setName(…)`, 22 more 0-cost methods under `GET /api/owners`) that regex loses at the first `)`,
and drops regex's phantoms (`Owner.toString` bound to `LocalDateTime.now().toString()`,
`VetFieldsDto` getters reached through a merged overload). No call is "not followed" on any of the
four petclinic snapshots.

Wider, for robustness and noise (no hand-scored truth; invariants checked by the reviewer: flowCc =
Σ cognitive = Σ hit increments, edges inside the flow, every hit line holds its keyword):

| repository | files | entry points | JavaParser | regex | calls not followed (entries with the chip) |
|---|---|---|---|---|---|
| client codebase A | 3 103 | 786 | 30 s | 131 s, 2.3 GB | 1 341 (163) |
| client codebase B | 1 071 | 142 | 19 s | — | 2 028 (84) |
| performance (course, two modules with one `PerformanceUtil`) | 136 | 46 | 2 s | 0.1 s | 0 |
| spring (course) | 158 | 45 | 2 s | — | 0 |
| petclinic workbench | 101 | 53 | 2 s | 0.4 s | 0 |

The first run of the reviewer's had client codebase A at 23 308 calls not followed on 704 of 786 entries —
noise, mostly library calls on locals and lambda parameters. Reading declarations off the source
(`infer`) brought it to the figure above; what remains is mostly DTO getters on receivers no rule
can type (Lombok getters on a type JavaParser cannot see, chains through library interfaces).

## Eval 3 — adversarial review

A separate agent (Opus) was told only to falsify "the new engine is equal or better than regex on
every case and never renders invalid output", with its own snippets, ten real repositories read in
place, and the renderer. Three passes; every repro it produced is now a corpus case (tagged
`[adversarial]`, `[adversarial 2]`, `[adversarial 3]`).

* **Pass 1 — 6 shapes worse than regex.** Two classes with one FQCN in two modules crashed the
  engine (NPE → whole snapshot fell back) or silently dropped the second module's controller; an
  implementation inherited from a superclass that does not itself implement the interface was
  dropped; project values arriving through library chains (`repo.findById(id).orElseThrow()
  .total()`, `ResponseEntity<Owner>.getBody()`) were dropped, some silently; the "not followed"
  chip was mostly noise (23 308 calls on client codebase A); `@Slf4j`/Lombok noise; the ↗ links read the
  merge-base's line numbers. Also, shared with regex: OpenAPI `default` stubs measured instead of
  the controller, a fully-qualified `@GetMapping` ignored, two listeners on one topic collapsing
  into one row, gitignored `target/` sources measured on one side only, an uncaught timeout,
  CR-only line endings. All fixed.
* **Pass 2 — 6 regressions introduced by the inference.** A repository's id type taken for the
  entity; lambdas on `Mono.just(order)` / `Flux.fromIterable(…)` silently dropped; a library
  functional type with project type arguments (`ItemProcessor<Order, Invoice>`) treated as
  all-library; the JDK-name filter swallowing a project call on a lambda parameter; every lambda
  parameter given the scope's element (`zipWith(mv, (p, v) -> …)`); a static import of a
  duplicated class bound to the other module's copy; container methods (`Page.getContent`,
  `List.isEmpty`) bound to a same-named method of the carried type; a two-type payload binding
  both; an untouched listener row churning when a second one appeared. All fixed — the ambiguous
  ones are now *reported*, not guessed.
* **Pass 3 — 1 shape worse than regex** (a lambda parameter typed by a generic project callee,
  `<T> each(List<T>, …, Consumer<T>)`: reported instead of followed) and three where both engines
  were wrong but the new one followed the wrong method (`map(order, OrderDto.class)` carrying the
  argument instead of the class literal; `map(x -> toDto(x))` not changing the element;
  `Specification<Owner>` / `RowMapper<Row>` parameters taken for the type argument). All fixed.

Still wrong in both engines, accepted and stated above: a generic base controller inherited by two
subclasses (`f3`: one row instead of two; JavaParser 3 by mixing both hooks, regex also one row),
and a template method on a concrete receiver (`h1`: JavaParser counts every override of the hook —
7 for a true 1 — where regex finds 0). Both follow from "every override may run", the stated
over-count; neither is a regression in kind (regex is wrong on both).

## Verdict

On the 93 hand-scored cases the JavaParser engine is exact on all and regex on 27. On real code,
every difference was read off the source and the JavaParser number was the right one. After three
adversarial passes no case remains where it is worse than regex, other than the two stated
over-count shapes where regex is also wrong. **The default is switched**: `--engine auto`
(JavaParser whenever `java` and `javac` are on the PATH, regex otherwise, and regex again on any
failure to fetch, build, parse or finish), with the engine named in the tab's lede and
`HR_COMPLEXITY_ENGINE=regex` to go back.

Debugging aid: `HR_CX_DEBUG=<text>` makes the engine print, for every call whose receiver contains
that text and that the solver could not bind, what `infer` concluded about the receiver.
