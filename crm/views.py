from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods


@staff_member_required
@require_GET
def dashboard(request):
    """Staff CRM shell at /admin/ — KPI widgets land in Phase 4."""
    return render(
        request,
        "crm/dashboard.html",
        {
            "page_title": "Olife CRM",
            "pipeline_status": "scaffold",
            "ga4_ready": False,
        },
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def commands(request):
    """
    Phase 5 backup control surface stub.
    POST body field `command` will hit the shared CommandRouter later.
    """
    result = None
    if request.method == "POST":
        command = (request.POST.get("command") or "").strip()
        result = {
            "accepted": bool(command),
            "command": command,
            "status": "queued_stub",
            "detail": "Command router wires up in Phase 5 (Telegram + this console).",
        }
        if request.headers.get("Accept") == "application/json":
            return JsonResponse(result)
    return render(
        request,
        "crm/commands.html",
        {"page_title": "Commands", "result": result},
    )
