# Review: 001 Core Library Extraction (v2)

## Findings

### 1. The cloud-consent contract is still internally inconsistent

V2 improves the privacy model, but it now defines three different rules for cloud execution. Rule 1 says cloud tools are allowed when the user passes `--tool ...` explicitly or the profile has `cloud_consent: true` (`planning/specs/001-core-library-extraction-v2.md:120-123`). The hard constraint later says network calls require both an explicit cloud tool and either `--cloud` or profile consent (`planning/specs/001-core-library-extraction-v2.md:843-845`). The acceptance criteria and CLI example follow the stricter version, where `--tool mineru|groq` still raises until `--cloud` is passed (`planning/specs/001-core-library-extraction-v2.md:836`, `planning/specs/001-core-library-extraction-v2.md:766-768`). The spec needs one rule here, because right now an implementation cannot satisfy all three simultaneously.

### 2. The router fallback chains still contradict themselves, and the PDF fallback conflicts with Rule 2

Rule 2 says `markdownify` is for local subprocess work on non-PDF formats (`planning/specs/001-core-library-extraction-v2.md:128-133`). But the PDF router still ends with an "absolute fallback" to `markdownify` for PDFs (`planning/specs/001-core-library-extraction-v2.md:445-451`). That is already in tension with the preceding branch that says missing LiteParse should raise `ToolNotInstalled`, so the fallback is either unreachable or it weakens the stated local-only/error behavior. The transcription router has the same structure: it says missing `coli` with no cloud consent should raise, then immediately lists an absolute fallback to `markdownify` (`planning/specs/001-core-library-extraction-v2.md:530-536`). These branches need to be normalized into one deterministic outcome per state.

### 3. `--force` is now part of the behavior, but it is not part of the actual API contract

The filer spec now says differing source hashes should produce a skip with a message telling the user to use `--force` (`planning/specs/001-core-library-extraction-v2.md:508`), and the CLI examples show `carrel paper convert ... --force` overwriting the filed paper (`planning/specs/001-core-library-extraction-v2.md:730-731`). But neither `ConvertOptions` nor `TranscribeOptions` includes a `force` field (`planning/specs/001-core-library-extraction-v2.md:231-258`), and `file_paper()` does not accept a `force` argument either (`planning/specs/001-core-library-extraction-v2.md:491-496`). The spec also never says where the source hash is stored for later comparison. This will force the implementation to invent behavior that should be specified up front.

### 4. Transcript naming is still not specified with the same determinism as paper naming

Rule 4 solves metadata fallback for papers only (`planning/specs/001-core-library-extraction-v2.md:143-161`). The transcript API still exposes just `transcript_filename(source, date, kind="recording")` (`planning/specs/001-core-library-extraction-v2.md:637-642`), while the examples expect richer outputs like `recording-2026-03-26.md` and `channel-name-topic-2026-03-26.md` (`planning/specs/001-core-library-extraction-v2.md:733-737`). There is still no deterministic fallback chain for topic extraction, channel naming, interview participant codes, or the case where the source filename is all the system has. That leaves one of the user-visible naming conventions transport-dependent again.

### 5. `vault init` no longer clearly creates the profile file that the rest of the spec expects

The scaffold section now says vault initialization creates folders, `.obsidian/`, templates, and the `.carrel/` directory (`planning/specs/001-core-library-extraction-v2.md:606-612`). But `env/profile.py` is still defined around reading and writing `.carrel/environment.json` (`planning/specs/001-core-library-extraction-v2.md:414-421`), and the reference `create-vault.js` explicitly writes that file during scaffolding (`skills/environment-setup/scripts/create-vault.js:160-183`). As written, `vault init` can produce a vault that satisfies path resolution but does not actually have the initial profile/state file the rest of the package expects.

### 6. `--format quiet` is still underspecified for commands whose result has no `path`

The acceptance criteria require all commands to support `--format quiet` (`planning/specs/001-core-library-extraction-v2.md:834`), but `cli/output.py` defines quiet mode as "just the path field if present" (`planning/specs/001-core-library-extraction-v2.md:658-662`). That works for convert/transcribe results, but not for `AuditResult`, `ScaffoldResult`, or likely `vault status`. The current wording leaves too much room for inconsistent command-specific behavior. The quiet contract should be defined per command family, or the spec should limit quiet mode to commands that naturally yield a single path.

## Open Questions

1. Is `--tool groq|mineru|gemini` alone sufficient consent, or is `--cloud` always additionally required unless profile consent is already true?
2. Where should the source hash live for idempotency checks: frontmatter, sidecar metadata, or `.carrel/` state?
3. Should `vault init` also create `.carrel/environment.json` with default profile values, or is profile creation intentionally deferred?

## Summary

V2 resolves most of the major contradictions from v1 and is much closer to implementation-ready. The remaining issues are mostly contract alignment problems: one cloud-consent rule, one router outcome per state, a real `--force` contract, deterministic transcript naming, and a fully specified initialized vault.
