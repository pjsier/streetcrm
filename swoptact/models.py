# SWOPTACT is a list of contacts with a history of their event attendance
# Copyright (C) 2015  Local Initiatives Support Corporation (LISC)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.db import models
from django.contrib.auth import models as auth_models
from django.contrib.admin.models import LogEntry
from django.utils import timezone

from swoptact import mixins, modelfields, managers
import phonenumbers

class SerializeableMixin:
    """
    Provides a .seralize method which serializes all properties on a model

    You should ensure when putting this on a model that all foreign keys also
    have this mixin added to them.

    This contains recursive functions, only use on models which you are sure
    do not contain cyclic relations.
    """

    def serialize(self):
        """ Provide a dictionary representation of model """
        # Get all the fields on the model
        fields = self._meta.fields

        # Produce the dictionary that will be built
        serialized = {}

        # Iterate over each field to and add the value to serialized.
        for field in fields:
            # Is the field in the serialize_exclude list
            if field.name in getattr(self, "SERIALIZE_EXCLUDE", []):
                continue

            # Get the value of the field
            value = getattr(self, field.name)

            # If it's a foreign key we should run serialize on the foreign model
            # and also provide a handy string representation
            if isinstance(value, models.Model):
                val_str = str(value)
                value = value.serialize()
                value['__str__'] = val_str

            # Phone numbers give back PhoneNumber objects, we want a string
            if isinstance(value, phonenumbers.PhoneNumber):
                if value.country_code == 1:
                    value = value.as_national
                else:
                    value = value.as_international

            # For all other values just add them as per usual
            serialized[field.name] = value

        return serialized
    
class PhoneNumber(models.Model):
    phone_number = modelfields.PhoneNumberField(null=True, blank=True,
                                                verbose_name="Phone Number")
    cell = models.BooleanField(default=False, blank=True,
                               verbose_name="Is this a cell phone?")
    owner = models.ForeignKey('Participant', related_name="Caller",
                                    blank=True, null=True)
    date_created = models.DateField(null=True, blank=True,
                                    default=timezone.now, verbose_name="Date Linked")
    def __str__(self):
        if self.phone_number is None:
            return None

        # Is it a US number
        if self.phone_number.country_code == 1:
            return self.phone_number.as_national
        else:
            return self.phone_number.as_international

class InspectMixin:
    """ Provides useful methods to inspect the model easily """

    @classmethod
    def get_field(cls, name):
        """ Gets a field by it's name """
        return cls._meta.get_field_by_name(name)[0]

class ArchiveAbstract(models.Model):
    """
    Provides archivability for models

    This does so by setting an "archived" field to the date and time
    that the model was archived at. If the field is null then the model
    is not archived.
    """

    # Date and Time model was archived at.
    archived = models.DateTimeField(null=True, blank=True)

    # Set the ArchiveManager as the manager for these models
    objects = managers.ArchiveManager()

    class Meta:
        abstract = True

    def delete(self):
        """ Archives the model """
        self.archived = timezone.now()
        self.save()

    def unarchive(self):
        """ Takes a model out of an archived state """
        self.archived = None
        self.save()


class Tag(ArchiveAbstract, SerializeableMixin, InspectMixin):
    """ Tags act as descriptors for such models as Event """
    name = models.CharField(max_length=15, unique=True, verbose_name="Tag")
    description = models.CharField(max_length=255, null=True,
                                   blank=True, verbose_name="Tag Description")
    date_created = models.DateField(null=True, blank=True,
                                    default=timezone.now, verbose_name="Date Tag Created")
    # Group which can use this tag
    group = models.ForeignKey(auth_models.Group,
                              verbose_name = "Group Assignment")

    # This should be put on Meta but sigh - issue #5793
    SERIALIZE_EXCLUDE = ["group"]

    def __str__(self):
        return self.name

class ActivityLog(LogEntry):
    class Meta:
        proxy = True
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Log"

class Institution(ArchiveAbstract, SerializeableMixin):
    name = models.CharField(max_length=255, unique=True,
                            verbose_name="Institution")
    inst_street_address = models.CharField(null=True, blank=True, max_length=1000,
                               verbose_name="Institution Street Address")
    inst_city_address = models.CharField(null=True, blank=True, max_length=255,
                               verbose_name="Institution City")
    inst_state_address = models.CharField(null=True, blank=True, max_length=255,
                               verbose_name="Institution State")
    inst_zipcode_address = models.CharField(null=True, blank=True, max_length=10,
                               verbose_name="Institution Zipcode")
    tags = models.ManyToManyField(Tag, blank=True,
                                  verbose_name="Institution Tags")
    contacts = models.ManyToManyField(
        "Participant",
        related_name="main_contact"
    )

    is_member = models.BooleanField(
        default=False,
        blank=True,
        verbose_name="Is this institution a member of SWOP?"
    )

    def __str__(self):
        return "{name}".format(name=self.name)

class Participant(ArchiveAbstract, SerializeableMixin):
    """ Representation of a person who can participate in a Event """
    name = models.CharField(max_length=255, verbose_name="Participant Name")
    email = models.EmailField(blank=True, verbose_name="Participant Email")
    participant_street_address = models.CharField(null=True, blank=True, max_length=1000,
                               verbose_name="Participant Street Address")
    participant_city_address = models.CharField(null=True, blank=True, max_length=255,
                               verbose_name="Participant City")
    participant_state_address = models.CharField(null=True, blank=True, max_length=255,
                               verbose_name="Participant State")
    participant_zipcode_address = models.CharField(null=True, blank=True, max_length=10,
                               verbose_name="Participant Zipcode")
    institution = models.ForeignKey(Institution, null=True, blank=True,
                                    verbose_name="Participant's Institution")
    title = models.CharField(null=True, blank=True, max_length=255,
                             help_text="e.g. Pastor, Director",
                             verbose_name="Participant's Title")

    def __str__(self):
        return self.name

    @property
    def events(self):
        """ List of all events participant is in """
        return Event.objects.filter(participants__in=[self]).all().order_by('-date')

class Event(ArchiveAbstract, mixins.AdminURLMixin, SerializeableMixin):
    class Meta:
        verbose_name = "action"
        verbose_name_plural = "actions"

    name = models.CharField(max_length=255,
                            verbose_name="Action Name",
                            help_text="The name includes an issue area and a topic.")
    description = models.CharField(max_length=255, null=True, blank=True,
                                   verbose_name="Action Description",
                                   help_text="Max length = 255 characters.<br> e.g." +
                                   "\"Met with housing stakeholders.\" ")
    date = models.DateField(null=True, blank=True,
                            verbose_name="Date of Action")
    time = modelfields.TwelveHourTimeField(null=True, blank=True,
                                           verbose_name="Time of Action")
    organizer = models.ForeignKey(Participant, related_name="Organizer",
                                  blank=True, null=True)
    location = models.CharField(max_length=255, blank=True,
                                verbose_name="Action Location")
    participants = models.ManyToManyField(Participant, blank=True)
    tags = models.ManyToManyField(Tag, blank=True,
                                  verbose_name="Action Tag(s)")
    issue_area = models.CharField(max_length=255, blank=True, null=True,
                                  verbose_name="Action Issue Area")
    is_prep = models.BooleanField(
        default=False,
        blank=True,
        verbose_name="This meeting is part of a major action:"
    )
    major_action = models.ForeignKey("self", null=True, blank=True)

    def __str__(self):
        return self.name


    def attendee_count(self):
        return self.participants.count()


