from django.db import models


class Employee(models.Model):
    id = models.CharField(primary_key=True, max_length=40)
    employee_id = models.CharField(max_length=40, blank=True, default="")
    name = models.CharField(max_length=160)
    supervisor = models.CharField(max_length=160, blank=True, default="")
    shift = models.CharField(max_length=40, default="shift1")
    status = models.CharField(max_length=40, default="Active")

    class Meta:
        db_table = "employees"


class Shift(models.Model):
    key = models.CharField(primary_key=True, max_length=40)
    label = models.CharField(max_length=80, default="")
    start = models.CharField(max_length=5, default="")
    end = models.CharField(max_length=5, default="")
    lunch_out = models.CharField(max_length=5, blank=True, default="")
    lunch_in = models.CharField(max_length=5, blank=True, default="")
    has_lunch = models.BooleanField(default=True)
    sat_start = models.CharField(max_length=5, blank=True, default="")
    sat_end = models.CharField(max_length=5, blank=True, default="")

    class Meta:
        db_table = "shifts"


class Record(models.Model):
    date = models.CharField(max_length=10)             # YYYY-MM-DD
    emp_id = models.CharField(max_length=40)
    time_in = models.CharField(max_length=5, blank=True, default="")
    lunch_out = models.CharField(max_length=5, blank=True, default="")
    lunch_in = models.CharField(max_length=5, blank=True, default="")
    time_out = models.CharField(max_length=5, blank=True, default="")
    day_status = models.CharField(max_length=60, blank=True, default="")
    missing_reason = models.CharField(max_length=60, blank=True, default="")
    remarks = models.CharField(max_length=400, blank=True, default="")
    category = models.CharField(max_length=40, blank=True, default="")

    class Meta:
        db_table = "records"
        unique_together = ("date", "emp_id")


class Status(models.Model):
    name = models.CharField(primary_key=True, max_length=60)

    class Meta:
        db_table = "statuses"
