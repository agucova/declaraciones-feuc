from peewee import (
    Model,
    Check,
    CharField,
    BooleanField,
    IntegerField,
    BigIntegerField,
    DateField,
    ForeignKeyField,
    SqliteDatabase,
)


db = SqliteDatabase("statements.sqlite")

# Model
class Person(Model):
    google_id = CharField(null=False, max_length=400)
    first_name = CharField(null=False)
    last_name = CharField(null=False)
    name = CharField(null=False)
    username = CharField(null=False)
    email = CharField(null=False)
    isRepresentative = BooleanField(
        null=False,
        help_text="Booleano representando si es un representante en el consejo o no.",
    )
    typeOfRepresentative = CharField(
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

    class Meta:
        database = db


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

    class Meta:
        database = db