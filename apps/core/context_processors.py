from django.conf import settings


def review_policy(request):
    return {"automatic_approval": settings.SAFERIDE_AUTO_APPROVAL}
