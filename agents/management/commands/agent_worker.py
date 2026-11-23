"""Long-running agent job worker — Phase 3A."""

from __future__ import annotations

import signal
import sys
import time
import traceback
from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from django.db import transaction

from agents.models import AgentJob


class Command(BaseCommand):
    help = "Poll AgentJob queue and execute jobs (Echo only in Phase 3A)."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._shutdown = False

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Process at most one job then exit (for tests).",
        )
        parser.add_argument(
            "--poll-interval",
            type=float,
            default=2.0,
            help="Seconds between polls when idle (default: 2).",
        )

    def handle(self, *args, **options):
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        once = options["once"]
        interval = options["poll_interval"]
        self.stdout.write("polling for jobs")
        self.stdout.flush()

        while not self._shutdown:
            job = self._claim_next_job()
            if job is None:
                if once:
                    break
                time.sleep(interval)
                continue

            self._run_job(job)
            if once:
                break

        self.stdout.write("worker shutdown")
        self.stdout.flush()

    def _handle_signal(self, signum, frame):
        self._shutdown = True
        self.stdout.write(f"signal {signum} received; finishing current work")
        self.stdout.flush()

    def _claim_next_job(self) -> AgentJob | None:
        with transaction.atomic():
            job = (
                AgentJob.objects.select_for_update(skip_locked=True)
                .filter(status=AgentJob.Status.PENDING)
                .order_by("created_at")
                .first()
            )
            if job is None:
                return None
            job.status = AgentJob.Status.RUNNING
            job.started_at = datetime.now(timezone.utc)
            job.save(update_fields=["status", "started_at"])
            return job

    def _run_job(self, job: AgentJob) -> None:
        started = time.perf_counter()
        self.stdout.write(f"job {job.id} RUNNING agent={job.agent_name}")
        self.stdout.flush()

        try:
            if job.agent_name != "echo":
                raise NotImplementedError("agent not implemented yet")

            from agents.graphs.echo import run_echo

            result = run_echo(job.command, thread_id=str(job.id))
            finished = datetime.now(timezone.utc)
            duration_ms = int((time.perf_counter() - started) * 1000)
            job.status = AgentJob.Status.SUCCEEDED
            job.result = result
            job.error = None
            job.finished_at = finished
            job.duration_ms = duration_ms
            job.save(
                update_fields=[
                    "status",
                    "result",
                    "error",
                    "finished_at",
                    "duration_ms",
                ]
            )
            self.stdout.write(
                f"job {job.id} SUCCEEDED duration_ms={duration_ms}"
            )
            self.stdout.flush()
        except Exception as exc:
            finished = datetime.now(timezone.utc)
            duration_ms = int((time.perf_counter() - started) * 1000)
            err = str(exc) or traceback.format_exc(limit=5)
            if isinstance(exc, NotImplementedError):
                err = "agent not implemented yet"
            job.status = AgentJob.Status.FAILED
            job.error = err[:8000]
            job.finished_at = finished
            job.duration_ms = duration_ms
            job.save(
                update_fields=["status", "error", "finished_at", "duration_ms"]
            )
            self.stdout.write(
                f"job {job.id} FAILED duration_ms={duration_ms} error={err[:200]}"
            )
            self.stdout.flush()
