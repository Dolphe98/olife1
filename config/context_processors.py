from django.conf import settings


def feature_flags(request):
    return {
        "FEATURE_GOOGLE_LOGIN": settings.FEATURE_GOOGLE_LOGIN,
        "FEATURE_COMMENTS": settings.FEATURE_COMMENTS,
        "FEATURE_GA4": settings.FEATURE_GA4,
        "FEATURE_STORE": settings.FEATURE_STORE,
        "FEATURE_NEWSLETTER": settings.FEATURE_NEWSLETTER,
        "STORE_URL": settings.STORE_URL,
        "GA4_MEASUREMENT_ID": settings.GA4_MEASUREMENT_ID,
    }
