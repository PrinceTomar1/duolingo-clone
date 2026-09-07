"""Declarative course content for the English -> Spanish course.

Content is data, not code: this module holds only vocabulary and sentence pairs.
Turning that data into the five exercise shapes is ``exercise_factory``'s job,
and writing it to the database is ``seed_data``'s. Keeping the three apart means
a content edit never risks the seeding logic.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WordPair:
    """One vocabulary item: the Spanish term and its English meaning."""

    es: str
    en: str


@dataclass(frozen=True)
class SentencePair:
    """One translatable sentence in both languages."""

    es: str
    en: str


@dataclass(frozen=True)
class SkillContent:
    """Everything needed to generate one skill's lessons."""

    title: str
    icon: str
    lesson_count: int
    vocabulary: list[WordPair]
    sentences: list[SentencePair]
    required_crowns_to_unlock: int = 1


@dataclass(frozen=True)
class UnitContent:
    """A themed group of skills, rendered as a coloured header bar."""

    title: str
    description: str
    color_hex: str
    skills: list[SkillContent] = field(default_factory=list)


COURSE_TITLE = "Spanish"
COURSE_FROM_LANGUAGE = "English"
COURSE_TO_LANGUAGE = "Spanish"


UNITS: list[UnitContent] = [
    UnitContent(
        title="Unit 1",
        description="Form basic sentences, greet people",
        color_hex="#58CC02",
        skills=[
            SkillContent(
                title="Greetings",
                icon="hand",
                lesson_count=3,
                vocabulary=[
                    WordPair("hola", "hello"),
                    WordPair("adiós", "goodbye"),
                    WordPair("gracias", "thank you"),
                    WordPair("por favor", "please"),
                    WordPair("buenos días", "good morning"),
                    WordPair("buenas noches", "good night"),
                    WordPair("perdón", "sorry"),
                    WordPair("hasta luego", "see you later"),
                    WordPair("sí", "yes"),
                    WordPair("no", "no"),
                ],
                sentences=[
                    SentencePair("Hola, buenos días.", "Hello, good morning."),
                    SentencePair("Gracias por favor.", "Thank you please."),
                    SentencePair("Adiós, hasta luego.", "Goodbye, see you later."),
                    SentencePair("Buenas noches, mamá.", "Good night, mom."),
                    SentencePair("Perdón, no hablo español.", "Sorry, I do not speak Spanish."),
                    SentencePair("Sí, gracias.", "Yes, thank you."),
                    SentencePair("Hola, ¿cómo estás?", "Hello, how are you?"),
                    SentencePair("Buenos días, señor.", "Good morning, sir."),
                ],
            ),
            SkillContent(
                title="Basics 1",
                icon="book",
                lesson_count=3,
                vocabulary=[
                    WordPair("el hombre", "the man"),
                    WordPair("la mujer", "the woman"),
                    WordPair("el niño", "the boy"),
                    WordPair("la niña", "the girl"),
                    WordPair("yo", "I"),
                    WordPair("tú", "you"),
                    WordPair("soy", "I am"),
                    WordPair("eres", "you are"),
                    WordPair("y", "and"),
                    WordPair("un", "a"),
                ],
                sentences=[
                    SentencePair("Yo soy un hombre.", "I am a man."),
                    SentencePair("Tú eres una mujer.", "You are a woman."),
                    SentencePair("El niño y la niña.", "The boy and the girl."),
                    SentencePair("Yo soy un niño.", "I am a boy."),
                    SentencePair("La mujer y el hombre.", "The woman and the man."),
                    SentencePair("Tú eres un niño.", "You are a boy."),
                    SentencePair("Yo soy una niña.", "I am a girl."),
                    SentencePair("El hombre es alto.", "The man is tall."),
                ],
            ),
            SkillContent(
                title="Basics 2",
                icon="sparkles",
                lesson_count=2,
                vocabulary=[
                    WordPair("come", "eats"),
                    WordPair("bebe", "drinks"),
                    WordPair("el agua", "the water"),
                    WordPair("el pan", "the bread"),
                    WordPair("la leche", "the milk"),
                    WordPair("ella", "she"),
                    WordPair("él", "he"),
                    WordPair("es", "is"),
                    WordPair("la manzana", "the apple"),
                    WordPair("nosotros", "we"),
                ],
                sentences=[
                    SentencePair("Ella come pan.", "She eats bread."),
                    SentencePair("Él bebe agua.", "He drinks water."),
                    SentencePair("Nosotros bebemos leche.", "We drink milk."),
                    SentencePair("La manzana es roja.", "The apple is red."),
                    SentencePair("Yo como una manzana.", "I eat an apple."),
                    SentencePair("Ella bebe leche.", "She drinks milk."),
                    SentencePair("El niño come pan.", "The boy eats bread."),
                    SentencePair("Nosotros comemos manzanas.", "We eat apples."),
                ],
            ),
            SkillContent(
                title="People",
                icon="users",
                lesson_count=2,
                vocabulary=[
                    WordPair("el amigo", "the friend"),
                    WordPair("el maestro", "the teacher"),
                    WordPair("el estudiante", "the student"),
                    WordPair("el doctor", "the doctor"),
                    WordPair("alto", "tall"),
                    WordPair("bajo", "short"),
                    WordPair("joven", "young"),
                    WordPair("viejo", "old"),
                    WordPair("el vecino", "the neighbor"),
                    WordPair("el jefe", "the boss"),
                ],
                sentences=[
                    SentencePair("Mi amigo es maestro.", "My friend is a teacher."),
                    SentencePair("El estudiante es joven.", "The student is young."),
                    SentencePair("El doctor es alto.", "The doctor is tall."),
                    SentencePair("Mi vecino es viejo.", "My neighbor is old."),
                    SentencePair("Ella es mi amiga.", "She is my friend."),
                    SentencePair("El jefe es bajo.", "The boss is short."),
                    SentencePair("Nosotros somos estudiantes.", "We are students."),
                    SentencePair("El maestro es joven.", "The teacher is young."),
                ],
            ),
        ],
    ),
    UnitContent(
        title="Unit 2",
        description="Order food, talk about family",
        color_hex="#1CB0F6",
        skills=[
            SkillContent(
                title="Food",
                icon="apple",
                lesson_count=3,
                vocabulary=[
                    WordPair("el arroz", "the rice"),
                    WordPair("el queso", "the cheese"),
                    WordPair("el huevo", "the egg"),
                    WordPair("la carne", "the meat"),
                    WordPair("el pescado", "the fish"),
                    WordPair("la sopa", "the soup"),
                    WordPair("la fruta", "the fruit"),
                    WordPair("el azúcar", "the sugar"),
                    WordPair("la cena", "the dinner"),
                    WordPair("el desayuno", "the breakfast"),
                ],
                sentences=[
                    SentencePair("Yo como arroz y carne.", "I eat rice and meat."),
                    SentencePair("El desayuno es un huevo.", "The breakfast is an egg."),
                    SentencePair("Ella cocina la sopa.", "She cooks the soup."),
                    SentencePair("Nosotros comemos pescado.", "We eat fish."),
                    SentencePair("La cena es queso y pan.", "The dinner is cheese and bread."),
                    SentencePair("El azúcar es blanco.", "The sugar is white."),
                    SentencePair("Yo bebo agua con la cena.", "I drink water with dinner."),
                    SentencePair("La fruta es dulce.", "The fruit is sweet."),
                ],
            ),
            SkillContent(
                title="Family",
                icon="home",
                lesson_count=3,
                vocabulary=[
                    WordPair("la madre", "the mother"),
                    WordPair("el padre", "the father"),
                    WordPair("el hermano", "the brother"),
                    WordPair("la hermana", "the sister"),
                    WordPair("el hijo", "the son"),
                    WordPair("la hija", "the daughter"),
                    WordPair("la abuela", "the grandmother"),
                    WordPair("el abuelo", "the grandfather"),
                    WordPair("la familia", "the family"),
                    WordPair("el esposo", "the husband"),
                ],
                sentences=[
                    SentencePair("Mi madre es doctora.", "My mother is a doctor."),
                    SentencePair("El padre come con la familia.", "The father eats with the family."),
                    SentencePair("Mi hermana es joven.", "My sister is young."),
                    SentencePair("El abuelo bebe agua.", "The grandfather drinks water."),
                    SentencePair("La abuela cocina la cena.", "The grandmother cooks dinner."),
                    SentencePair("Mi hermano es alto.", "My brother is tall."),
                    SentencePair("La familia come pescado.", "The family eats fish."),
                    SentencePair("Su hija es maestra.", "Their daughter is a teacher."),
                ],
            ),
            SkillContent(
                title="Animals",
                icon="paw",
                lesson_count=2,
                vocabulary=[
                    WordPair("el gato", "the cat"),
                    WordPair("el perro", "the dog"),
                    WordPair("el pájaro", "the bird"),
                    WordPair("el caballo", "the horse"),
                    WordPair("la vaca", "the cow"),
                    WordPair("el ratón", "the mouse"),
                    WordPair("la araña", "the spider"),
                    WordPair("el oso", "the bear"),
                    WordPair("la tortuga", "the turtle"),
                    WordPair("el pato", "the duck"),
                ],
                sentences=[
                    SentencePair("El gato bebe leche.", "The cat drinks milk."),
                    SentencePair("Mi perro es viejo.", "My dog is old."),
                    SentencePair("El caballo come manzanas.", "The horse eats apples."),
                    SentencePair("La vaca es grande.", "The cow is big."),
                    SentencePair("El pájaro bebe agua.", "The bird drinks water."),
                    SentencePair("La tortuga es lenta.", "The turtle is slow."),
                    SentencePair("El oso come pescado.", "The bear eats fish."),
                    SentencePair("El pato y el ratón.", "The duck and the mouse."),
                ],
            ),
            SkillContent(
                title="Colors",
                icon="palette",
                lesson_count=2,
                vocabulary=[
                    WordPair("rojo", "red"),
                    WordPair("azul", "blue"),
                    WordPair("verde", "green"),
                    WordPair("amarillo", "yellow"),
                    WordPair("negro", "black"),
                    WordPair("blanco", "white"),
                    WordPair("naranja", "orange"),
                    WordPair("morado", "purple"),
                    WordPair("gris", "grey"),
                    WordPair("rosa", "pink"),
                ],
                sentences=[
                    SentencePair("El gato es negro.", "The cat is black."),
                    SentencePair("Mi casa es blanca.", "My house is white."),
                    SentencePair("El pájaro es azul.", "The bird is blue."),
                    SentencePair("La manzana es verde.", "The apple is green."),
                    SentencePair("El queso es amarillo.", "The cheese is yellow."),
                    SentencePair("Su coche es rojo.", "Their car is red."),
                    SentencePair("La flor es morada.", "The flower is purple."),
                    SentencePair("El caballo es gris.", "The horse is grey."),
                ],
            ),
        ],
    ),
    UnitContent(
        title="Unit 3",
        description="Travel, tell the time, find places",
        color_hex="#CE82FF",
        skills=[
            SkillContent(
                title="Travel",
                icon="plane",
                lesson_count=3,
                vocabulary=[
                    WordPair("el aeropuerto", "the airport"),
                    WordPair("el tren", "the train"),
                    WordPair("el coche", "the car"),
                    WordPair("el boleto", "the ticket"),
                    WordPair("la maleta", "the suitcase"),
                    WordPair("el hotel", "the hotel"),
                    WordPair("el mapa", "the map"),
                    WordPair("el pasaporte", "the passport"),
                    WordPair("el autobús", "the bus"),
                    WordPair("viajar", "to travel"),
                ],
                sentences=[
                    SentencePair("Yo viajo en tren.", "I travel by train."),
                    SentencePair("Mi maleta es azul.", "My suitcase is blue."),
                    SentencePair("El hotel es grande.", "The hotel is big."),
                    SentencePair("Necesito un boleto.", "I need a ticket."),
                    SentencePair("El aeropuerto es nuevo.", "The airport is new."),
                    SentencePair("Ella tiene el pasaporte.", "She has the passport."),
                    SentencePair("Nosotros viajamos en autobús.", "We travel by bus."),
                    SentencePair("El mapa está en el coche.", "The map is in the car."),
                ],
            ),
            SkillContent(
                title="Numbers",
                icon="hash",
                lesson_count=2,
                vocabulary=[
                    WordPair("uno", "one"),
                    WordPair("dos", "two"),
                    WordPair("tres", "three"),
                    WordPair("cuatro", "four"),
                    WordPair("cinco", "five"),
                    WordPair("seis", "six"),
                    WordPair("siete", "seven"),
                    WordPair("ocho", "eight"),
                    WordPair("nueve", "nine"),
                    WordPair("diez", "ten"),
                ],
                sentences=[
                    SentencePair("Tengo dos hermanos.", "I have two brothers."),
                    SentencePair("Hay cinco gatos.", "There are five cats."),
                    SentencePair("Necesito tres boletos.", "I need three tickets."),
                    SentencePair("Ella tiene cuatro manzanas.", "She has four apples."),
                    SentencePair("Somos seis en la familia.", "We are six in the family."),
                    SentencePair("El hotel tiene diez pisos.", "The hotel has ten floors."),
                    SentencePair("Compro ocho huevos.", "I buy eight eggs."),
                    SentencePair("Hay nueve estudiantes.", "There are nine students."),
                ],
            ),
            SkillContent(
                title="Time",
                icon="clock",
                lesson_count=2,
                vocabulary=[
                    WordPair("el día", "the day"),
                    WordPair("la noche", "the night"),
                    WordPair("la mañana", "the morning"),
                    WordPair("la tarde", "the afternoon"),
                    WordPair("la hora", "the hour"),
                    WordPair("el minuto", "the minute"),
                    WordPair("hoy", "today"),
                    WordPair("mañana", "tomorrow"),
                    WordPair("ayer", "yesterday"),
                    WordPair("la semana", "the week"),
                ],
                sentences=[
                    SentencePair("Hoy es un buen día.", "Today is a good day."),
                    SentencePair("Yo trabajo en la mañana.", "I work in the morning."),
                    SentencePair("Mañana viajo a Madrid.", "Tomorrow I travel to Madrid."),
                    SentencePair("La cena es en la noche.", "Dinner is at night."),
                    SentencePair("Ayer comí pescado.", "Yesterday I ate fish."),
                    SentencePair("Espero una hora.", "I wait one hour."),
                    SentencePair("La semana tiene siete días.", "The week has seven days."),
                    SentencePair("Estudio en la tarde.", "I study in the afternoon."),
                ],
            ),
            SkillContent(
                title="Places",
                icon="map-pin",
                lesson_count=2,
                vocabulary=[
                    WordPair("la ciudad", "the city"),
                    WordPair("el pueblo", "the town"),
                    WordPair("la casa", "the house"),
                    WordPair("la escuela", "the school"),
                    WordPair("el mercado", "the market"),
                    WordPair("el parque", "the park"),
                    WordPair("la playa", "the beach"),
                    WordPair("el restaurante", "the restaurant"),
                    WordPair("la tienda", "the store"),
                    WordPair("la calle", "the street"),
                ],
                sentences=[
                    SentencePair("La ciudad es grande.", "The city is big."),
                    SentencePair("Voy al mercado hoy.", "I go to the market today."),
                    SentencePair("Mi casa está en la calle.", "My house is on the street."),
                    SentencePair("Los niños van a la escuela.", "The children go to school."),
                    SentencePair("Comemos en el restaurante.", "We eat at the restaurant."),
                    SentencePair("El parque es bonito.", "The park is pretty."),
                    SentencePair("La playa está cerca.", "The beach is near."),
                    SentencePair("Compro fruta en la tienda.", "I buy fruit at the store."),
                ],
            ),
        ],
    ),
]


ACHIEVEMENTS: list[dict[str, object]] = [
    {
        "code": "FIRST_LESSON",
        "metric": "lessons_completed",
        "title": "Wildfire",
        "description": "Complete your very first lesson",
        "icon": "flame",
        "color_hex": "#FF9600",
        "target": 1,
    },
    {
        "code": "STREAK_7",
        "metric": "longest_streak",
        "title": "Sage",
        "description": "Reach a 7 day streak",
        "icon": "calendar",
        "color_hex": "#CE82FF",
        "target": 7,
    },
    {
        "code": "XP_1000",
        "metric": "total_xp",
        "title": "Scholar",
        "description": "Earn 1,000 total XP",
        "icon": "graduation-cap",
        "color_hex": "#1CB0F6",
        "target": 1000,
    },
    {
        "code": "CROWNS_20",
        "metric": "total_crowns",
        "title": "Champion",
        "description": "Collect 20 crowns",
        "icon": "crown",
        "color_hex": "#FFC800",
        "target": 20,
    },
    {
        "code": "PERFECT_5",
        "metric": "perfect_lessons",
        "title": "Sharpshooter",
        "description": "Finish 5 lessons without losing a heart",
        "icon": "target",
        "color_hex": "#58CC02",
        "target": 5,
    },
    {
        "code": "STREAK_30",
        "metric": "longest_streak",
        "title": "Legendary",
        "description": "Reach a 30 day streak",
        "icon": "trophy",
        "color_hex": "#FF4B4B",
        "target": 30,
    },
]
