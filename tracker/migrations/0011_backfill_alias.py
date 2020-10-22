# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-01-19 03:35
from __future__ import unicode_literals

import random
import logging
from itertools import groupby

from django.db import migrations

logger = logging.getLogger(__name__)

def fill_in_alias(Donor, donor):
    existing = set(d.alias_num for d in Donor.objects.filter(alias=donor.alias))
    available = [i for i in range(1000, 10000) if i not in existing]
    if not available:
        logger.warning(
            f'Could not set alias `{donor.alias}` because the namespace was full'
        )
        donor.alias = None
        donor.alias_num = None
    else:
        donor.alias_num = random.choice(available)

def strip_whitespace(apps, schema_editor):
    Donation = apps.get_model('tracker', 'Donation')
    db_alias = schema_editor.connection.alias
    donations = Donation.objects.using(db_alias).exclude(requestedalias='')
    for donation in donations:
        stripped = donation.requestedalias.strip()
        if stripped != donation.requestedalias:
            donation.requestedalias = stripped
            donation.save()

def reapply_alias(apps, schema_editor):
    Donation = apps.get_model('tracker', 'Donation')
    Donor = apps.get_model('tracker', 'Donor')
    db_alias = schema_editor.connection.alias
    donations = Donation.objects.using(db_alias).filter(transactionstate='COMPLETED') \
                    .exclude(requestedalias='').order_by('donor', 'timereceived').select_related('donor')
    for donor, donations in groupby(donations, lambda d: d.donor):
        donation = list(donations)[-1]
        if donation.requestedalias != donation.donor.alias:
            donation.donor.alias = donation.requestedalias
            donation.donor.alias_num = None
            fill_in_alias(Donor, donation.donor)
            donation.donor.verified_alias = False
            donation.donor.save()


def fill_in_missing_no(apps, schema_editor):
    Donor = apps.get_model('tracker', 'Donor')
    db_alias = schema_editor.connection.alias
    donors = Donor.objects.using(db_alias).exclude(alias=None).filter(alias_num=None)
    for donor in donors:
        fill_in_alias(Donor, donor)
        donor.save()


def no_op(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0010_add_alias_num'),
    ]

    operations = [
        migrations.RunPython(strip_whitespace, no_op, elidable=True),
        migrations.RunPython(reapply_alias, no_op, elidable=True),
        migrations.RunPython(fill_in_missing_no, no_op, elidable=True),
    ]
