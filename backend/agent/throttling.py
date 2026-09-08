from rest_framework.throttling import SimpleRateThrottle


class InterviewRateThrottle(SimpleRateThrottle):
    """20 questions per IP per hour.

    Counts live in the database cache so all gunicorn workers share one
    tally. Behind Render's proxy, ``get_ident`` reads the client address
    from X-Forwarded-For.
    """

    scope = "interview"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }
