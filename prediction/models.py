from django.db import models
from django.contrib.auth.models import User


# ============================================================
# PREDICTION HISTORY
# ============================================================

class PredictionHistory(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    age = models.FloatField()

    gender = models.IntegerField()

    bmi = models.FloatField()

    systolic_bp = models.FloatField()

    serum_creatinine = models.FloatField()

    blood_urea_nitrogen = models.FloatField()

    egfr = models.FloatField()

    urine_albumin = models.FloatField()

    albumin_creatinine_ratio = models.FloatField()

    diabetes = models.CharField(
        max_length=10
    )

    prediction = models.CharField(
        max_length=100
    )

    confidence = models.FloatField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.prediction}"
