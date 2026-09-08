from django.db import models


class InterviewLog(models.Model):
    """One question and answer from the interview agent.

    Cory reads these to see what visitors actually ask. The visitor's IP is
    stored only as a salted hash, so the table holds no raw addresses.
    """

    session_id = models.UUIDField(db_index=True)
    question = models.TextField()
    answer = models.TextField()
    ip_hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "interview log"
        verbose_name_plural = "interview logs"

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} - {self.question[:60]}"
