from django.core.management.base import BaseCommand, CommandError

from agents.models import AgentJob


class Command(BaseCommand):
    help = "Enqueue an agent job (PENDING) and print its UUID."

    def add_arguments(self, parser):
        parser.add_argument("agent_name", type=str, help="Agent name (e.g. echo)")
        parser.add_argument("command", type=str, help="Command / prompt text")
        parser.add_argument(
            "--created-by",
            choices=[c.value for c in AgentJob.CreatedBy],
            default=AgentJob.CreatedBy.CLI,
            help="Job source (default: cli)",
        )

    def handle(self, *args, **options):
        agent_name = (options["agent_name"] or "").strip()
        command = options["command"]
        if not agent_name:
            raise CommandError("agent_name is required")
        if not (command or "").strip():
            raise CommandError("command is required")

        job = AgentJob.objects.create(
            agent_name=agent_name,
            command=command,
            status=AgentJob.Status.PENDING,
            created_by=options["created_by"],
        )
        self.stdout.write(str(job.id))
