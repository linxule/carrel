from __future__ import annotations

import argparse
from pathlib import Path

from .constants import SENSITIVITY, TRUST_LEVELS
from .ingestion import (
    cmd_batch_convert,
    cmd_batch_transcribe,
    cmd_capture_url,
    cmd_convert_file,
    cmd_google_export,
    cmd_policy_explain,
    cmd_transcript_create,
)
from .maintenance import (
    cmd_automation_configure,
    cmd_feedback_export,
    cmd_mirror_write,
    cmd_reflection_append,
    cmd_share_generate,
    cmd_trust_check,
    cmd_trust_list,
    cmd_trust_show,
)
from .setup_env import cmd_env_doctor, cmd_env_fix, cmd_env_validate, cmd_vault_init


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="carrel.py")
    sub = parser.add_subparsers(dest="group", required=True)

    vault = sub.add_parser("vault")
    vault_sub = vault.add_subparsers(dest="command", required=True)
    vault_init = vault_sub.add_parser("init")
    vault_init.add_argument("path", type=Path)
    vault_init.add_argument("--format", choices=["human", "json"], default="human")
    vault_init.set_defaults(func=cmd_vault_init)

    env = sub.add_parser("env")
    env_sub = env.add_subparsers(dest="command", required=True)
    env_validate = env_sub.add_parser("validate")
    env_validate.add_argument("--vault", type=Path, required=True)
    env_validate.add_argument("--format", choices=["human", "json"], default="human")
    env_validate.set_defaults(func=cmd_env_validate)
    env_fix = env_sub.add_parser("fix")
    env_fix.add_argument("--vault", type=Path, required=True)
    env_fix.add_argument("--dry-run", action="store_true")
    env_fix.add_argument("--format", choices=["human", "json"], default="human")
    env_fix.set_defaults(func=cmd_env_fix)
    env_doctor = env_sub.add_parser("doctor")
    env_doctor.add_argument("--project-path", type=Path)
    env_doctor.add_argument("--format", choices=["human", "json"], default="human")
    env_doctor.set_defaults(func=cmd_env_doctor)

    policy = sub.add_parser("policy")
    policy_sub = policy.add_subparsers(dest="command", required=True)
    explain = policy_sub.add_parser("explain")
    explain.add_argument("--tool-class", choices=["convert", "transcribe"], required=True)
    explain.add_argument("--requested-tool")
    explain.add_argument("--available-tools", default="")
    explain.add_argument("--sensitivity", choices=sorted(SENSITIVITY), default="medium")
    explain.add_argument("--cloud-consent", action="store_true")
    explain.set_defaults(func=cmd_policy_explain)

    capture = sub.add_parser("capture")
    capture_sub = capture.add_subparsers(dest="command", required=True)
    capture_url = capture_sub.add_parser("url")
    capture_url.add_argument("url")
    capture_url.add_argument("--vault", type=Path, required=True)
    capture_url.add_argument("--title")
    capture_url.add_argument("--content")
    capture_url.add_argument("--dry-run", action="store_true")
    capture_url.add_argument("--force", action="store_true")
    capture_url.set_defaults(func=cmd_capture_url)

    convert = sub.add_parser("convert")
    convert_sub = convert.add_subparsers(dest="command", required=True)
    convert_file = convert_sub.add_parser("file")
    convert_file.add_argument("file", type=Path)
    convert_file.add_argument("--vault", type=Path, required=True)
    convert_file.add_argument("--tool")
    convert_file.add_argument("--sensitivity", choices=sorted(SENSITIVITY))
    convert_file.add_argument("--content")
    convert_file.add_argument("--dry-run", action="store_true")
    convert_file.add_argument("--explain", action="store_true")
    convert_file.add_argument("--force", action="store_true")
    convert_file.set_defaults(func=cmd_convert_file)

    google = sub.add_parser("google")
    google_sub = google.add_subparsers(dest="command", required=True)
    google_export = google_sub.add_parser("export")
    google_export.add_argument("url")
    google_export.add_argument("--vault", type=Path, required=True)
    google_export.add_argument("--export-format", choices=["docx", "pdf", "txt", "html"], default="docx")
    google_export.add_argument("--keep-export", action="store_true")
    google_export.add_argument("--tool")
    google_export.add_argument("--sensitivity", choices=sorted(SENSITIVITY))
    google_export.add_argument("--content")
    google_export.add_argument("--title")
    google_export.add_argument("--dry-run", action="store_true")
    google_export.add_argument("--explain", action="store_true")
    google_export.add_argument("--force", action="store_true")
    google_export.set_defaults(func=cmd_google_export)

    batch = sub.add_parser("batch")
    batch_sub = batch.add_subparsers(dest="command", required=True)
    batch_convert = batch_sub.add_parser("convert")
    batch_convert.add_argument("folder", type=Path)
    batch_convert.add_argument("--vault", type=Path, required=True)
    batch_convert.add_argument("--unattended", action="store_true")
    batch_convert.add_argument("--tool")
    batch_convert.add_argument("--sensitivity", choices=sorted(SENSITIVITY))
    batch_convert.add_argument("--dry-run", action="store_true")
    batch_convert.add_argument("--explain", action="store_true")
    batch_convert.add_argument("--force", action="store_true")
    batch_convert.add_argument("--format", choices=["human", "json"], default="human")
    batch_convert.set_defaults(func=cmd_batch_convert)
    batch_transcribe = batch_sub.add_parser("transcribe")
    batch_transcribe.add_argument("folder", type=Path)
    batch_transcribe.add_argument("--vault", type=Path, required=True)
    batch_transcribe.add_argument("--unattended", action="store_true")
    batch_transcribe.add_argument("--kind", default="recording")
    batch_transcribe.add_argument("--tool")
    batch_transcribe.add_argument("--sensitivity", choices=sorted(SENSITIVITY))
    batch_transcribe.add_argument("--content")
    batch_transcribe.add_argument("--dry-run", action="store_true")
    batch_transcribe.add_argument("--explain", action="store_true")
    batch_transcribe.add_argument("--force", action="store_true")
    batch_transcribe.add_argument("--format", choices=["human", "json"], default="human")
    batch_transcribe.set_defaults(func=cmd_batch_transcribe)

    transcript = sub.add_parser("transcript")
    transcript_sub = transcript.add_subparsers(dest="command", required=True)
    transcript_create = transcript_sub.add_parser("create")
    transcript_create.add_argument("source")
    transcript_create.add_argument("--vault", type=Path, required=True)
    transcript_create.add_argument("--kind", default="recording")
    transcript_create.add_argument("--tool")
    transcript_create.add_argument("--sensitivity", choices=sorted(SENSITIVITY))
    transcript_create.add_argument("--content")
    transcript_create.add_argument("--dry-run", action="store_true")
    transcript_create.add_argument("--explain", action="store_true")
    transcript_create.add_argument("--force", action="store_true")
    transcript_create.set_defaults(func=cmd_transcript_create)

    reflection = sub.add_parser("reflection")
    reflection_sub = reflection.add_subparsers(dest="command", required=True)
    reflection_append = reflection_sub.add_parser("append")
    reflection_append.add_argument("--vault", type=Path, required=True)
    reflection_append.set_defaults(func=cmd_reflection_append)

    mirror = sub.add_parser("mirror")
    mirror_sub = mirror.add_subparsers(dest="command", required=True)
    mirror_write = mirror_sub.add_parser("write")
    mirror_write.add_argument("--vault", type=Path, required=True)
    mirror_write.add_argument("--force", action="store_true")
    mirror_write.set_defaults(func=cmd_mirror_write)

    feedback = sub.add_parser("feedback")
    feedback_sub = feedback.add_subparsers(dest="command", required=True)
    feedback_export = feedback_sub.add_parser("export")
    feedback_export.add_argument("--vault", type=Path, required=True)
    feedback_export.add_argument("--redact-list", type=Path, required=True)
    feedback_export.set_defaults(func=cmd_feedback_export)

    share = sub.add_parser("share")
    share_sub = share.add_subparsers(dest="command", required=True)
    share_generate = share_sub.add_parser("generate")
    share_generate.add_argument("--vault", type=Path, required=True)
    share_generate.add_argument("--for", dest="name", required=True)
    share_generate.add_argument("--sensitivity", choices=sorted(SENSITIVITY), default="medium")
    share_generate.add_argument("--mode", choices=["quick", "full"], default="quick")
    share_generate.set_defaults(func=cmd_share_generate)

    trust = sub.add_parser("trust")
    trust_sub = trust.add_subparsers(dest="command", required=True)
    trust_check = trust_sub.add_parser("check")
    trust_check.add_argument("action")
    trust_check.add_argument("--vault", type=Path, required=True)
    trust_check.add_argument("--trust-level", choices=sorted(TRUST_LEVELS))
    trust_check.add_argument("--format", choices=["human", "json"], default="human")
    trust_check.set_defaults(func=cmd_trust_check)
    trust_list = trust_sub.add_parser("list")
    trust_list.add_argument("--vault", type=Path, required=True)
    trust_list.add_argument("--trust-level", choices=sorted(TRUST_LEVELS))
    trust_list.add_argument("--format", choices=["human", "json"], default="human")
    trust_list.set_defaults(func=cmd_trust_list)
    trust_show = trust_sub.add_parser("show")
    trust_show.add_argument("--vault", type=Path, required=True)
    trust_show.add_argument("--format", choices=["human", "json"], default="human")
    trust_show.set_defaults(func=cmd_trust_show)

    automation = sub.add_parser("automation")
    automation_sub = automation.add_subparsers(dest="command", required=True)
    automation_configure = automation_sub.add_parser("configure")
    automation_configure.add_argument("--vault", type=Path, required=True)
    automation_configure.add_argument("--enabled", choices=["true", "false"], required=True)
    automation_configure.add_argument("--trust-level", choices=sorted(TRUST_LEVELS), required=True)
    automation_configure.add_argument("--schedule", choices=["daily", "weekdays", "weekly"], required=True)
    automation_configure.add_argument("--review-cadence", choices=["monthly", "quarterly", "biannual"], required=True)
    automation_configure.add_argument("--model", choices=["sonnet", "opus"], default="sonnet")
    automation_configure.add_argument("--inbox-processing", choices=["true", "false"])
    automation_configure.add_argument("--vault-health", choices=["true", "false"])
    automation_configure.add_argument("--cross-linking", choices=["true", "false"])
    automation_configure.add_argument("--gap-analysis", choices=["true", "false"])
    automation_configure.add_argument("--draft-feedback", choices=["true", "false"])
    automation_configure.add_argument("--reflection-synthesis", choices=["true", "false"])
    automation_configure.add_argument("--wiki-maintenance", choices=["true", "false"])
    automation_configure.set_defaults(func=cmd_automation_configure)

    return parser
