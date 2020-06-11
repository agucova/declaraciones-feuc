from peewee import (
    Model,
    Check,
    CharField,
    BooleanField,
    IntegerField,
    DateField,
    ForeignKeyField,
    SqliteDatabase,
    DateTimeField,
)


# TODO: #1 Migrate to PostgreSQL or MariaDB
db = SqliteDatabase("statements.sqlite")


# Model
class Organization(Model):
    name = CharField(
        max_length=120,
        null=False,
        help_text="Nombre de la organización. Ej: Centro de Alumnos de Ingeniería",
    )
    acronym = CharField(
        max_length=12, null=False, help_text="Acrónimo de la organización. Ej: CAi"
    )
    type_of_org = CharField(
        max_length=80,
        null=False,
        help_text="Tipo de organización. Ej: Centro de Alumnos",
    )

    class Meta:
        database = db


class Person(Model):
    google_id = CharField(null=False, max_length=400)
    first_name = CharField(null=False)
    last_name = CharField(null=False)
    name = CharField(null=False)
    username = CharField(null=False)
    email = CharField(null=False)
    is_representative = BooleanField(
        null=False, help_text="Si es un representante en el consejo o no.",
    )
    type_of_representative = CharField(
        null=True,
        max_length=120,
        help_text="Tipo de representante. Ej. Consejero Territorial",
    )
    territory = CharField(
        null=True,
        max_length=120,
        help_text="Territorio Político. Ej. Ciencias de la Salud",
    )
    carreer = CharField(
        null=True, max_length=120, help_text="Carrera. Ej. Fonoaudiología"
    )
    year = IntegerField(
        null=True,
        constraints=[Check("3000 > year > 2018")],
        help_text="Año del cargo tomado por el representante. Se aproxima según el año completo, si empieza en Diciembre 2019 es 2020.",
    )
    is_active = BooleanField(null=False)
    is_authenticated = BooleanField(null=False)
    is_superuser = BooleanField(null=True)
    member_of = ForeignKeyField(
        Organization,
        backref="members",
        help_text="A qué organización pertenece/representa.",
        null=True,
    )
    admin_of = ForeignKeyField(
        Organization,
        backref="admins",
        help_text="Administrador de la organizacion.",
        null=True,
    )

    class Meta:
        database = db


# TODO: #2 Implementar conexión a S3 o blobs
class Statement(Model):
    title = CharField(
        max_length=400,
        null=False,
        help_text='Título de la declaración. Por favor no incluir "Declaración sobre".',
    )
    date_added = DateField(
        null=False, help_text="Fecha en la que fue añadida la declaración a la db."
    )
    submited_by = ForeignKeyField(
        Person,
        backref="statements",
        help_text="Foreign key de quién agregó la declaración.",
    )
    organization_affiliated = ForeignKeyField(  # TODO: #9 Implement Many to Many
        Organization,
        backref="statements",
        help_text="Organizacion afiliada a la declaración.",
    )

    last_updated = DateTimeField(null=False)

    class Meta:
        database = db
