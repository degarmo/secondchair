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


class SpeechRateThrottle(SimpleRateThrottle):
    """60 spoken answers per IP per hour.

    Looser than the question limit, because replaying a cached answer is
    free, but still bounded: synthesis is the part of the site that costs
    money per use.
    """

    scope = "speech"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }
