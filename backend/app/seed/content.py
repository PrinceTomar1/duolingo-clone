"""Declarative course content: vocabulary and sentence pairs, per course.

Content is data, not code: this module holds only vocabulary and sentence pairs.
Turning that data into the five exercise shapes is ``exercise_factory``'s job,
and writing it to the database is ``seed_data``'s. Keeping the three apart means
a content edit never risks the seeding logic.

Two courses live here (Spanish and French), each pairing its vocabulary with a
``LanguageProfile`` -- the handful of language-specific facts (what to call the
language in a generated prompt, which words are articles worth stripping from a
multiple-choice option, which words are too grammatical to make a good
fill-in-the-blank target) that ``exercise_factory`` needs and would otherwise
have had hardcoded to Spanish.
"""

from dataclasses import dataclass, field

from app.seed.exercise_factory import LanguageProfile


@dataclass(frozen=True)
class WordPair:
    """One vocabulary item: the course's target-language term and its English meaning."""

    target: str
    english: str


@dataclass(frozen=True)
class SentencePair:
    """One translatable sentence in both languages."""

    target: str
    english: str


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


@dataclass(frozen=True)
class CourseContent:
    """One full course: its language pairing, its content, and how to drill it."""

    title: str
    from_language: str
    to_language: str
    profile: LanguageProfile
    units: list[UnitContent]


SPANISH_PROFILE = LanguageProfile(
    name="Spanish",
    stop_words=frozenset(
        {
            "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "de", "en",
            "a", "al", "del", "es", "son", "mi", "su", "con", "que", "hay",
        }
    ),
    articles=("el ", "la ", "los ", "las "),
)

SPANISH_UNITS: list[UnitContent] = [
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

SPANISH_COURSE = CourseContent(
    title="Spanish",
    from_language="English",
    to_language="Spanish",
    profile=SPANISH_PROFILE,
    units=SPANISH_UNITS,
)


FRENCH_PROFILE = LanguageProfile(
    name="French",
    # French articles/function words that make poor multiple-choice or
    # fill-blank targets, mirroring the Spanish list's role.
    stop_words=frozenset(
        {
            "le", "la", "les", "l'", "un", "une", "des", "et", "ou", "de", "du",
            "à", "au", "aux", "est", "sont", "mon", "ma", "son", "sa", "avec", "que",
        }
    ),
    articles=("le ", "la ", "les ", "l'"),
)

FRENCH_UNITS: list[UnitContent] = [
    UnitContent(
        title="Unit 1",
        description="Say hello, meet people",
        color_hex="#CE82FF",
        skills=[
            SkillContent(
                title="Greetings",
                icon="hand",
                lesson_count=2,
                vocabulary=[
                    WordPair("bonjour", "hello"),
                    WordPair("au revoir", "goodbye"),
                    WordPair("merci", "thank you"),
                    WordPair("s'il vous plaît", "please"),
                    WordPair("bonsoir", "good evening"),
                    WordPair("bonne nuit", "good night"),
                    WordPair("pardon", "sorry"),
                    WordPair("à bientôt", "see you soon"),
                    WordPair("oui", "yes"),
                    WordPair("non", "no"),
                ],
                sentences=[
                    SentencePair("Bonjour, merci.", "Hello, thank you."),
                    SentencePair("Au revoir, à bientôt.", "Goodbye, see you soon."),
                    SentencePair("Pardon, s'il vous plaît.", "Sorry, please."),
                    SentencePair("Bonsoir, bonne nuit.", "Good evening, good night."),
                    SentencePair("Oui, merci beaucoup.", "Yes, thank you very much."),
                    SentencePair("Bonjour, comment ça va?", "Hello, how are you?"),
                    SentencePair("Non, merci.", "No, thank you."),
                    SentencePair("Bonjour madame.", "Hello madam."),
                ],
            ),
            SkillContent(
                title="Basics 1",
                icon="book",
                lesson_count=2,
                vocabulary=[
                    WordPair("l'homme", "the man"),
                    WordPair("la femme", "the woman"),
                    WordPair("le garçon", "the boy"),
                    WordPair("la fille", "the girl"),
                    WordPair("je", "I"),
                    WordPair("tu", "you"),
                    WordPair("je suis", "I am"),
                    WordPair("tu es", "you are"),
                    WordPair("et", "and"),
                    WordPair("un", "a"),
                ],
                sentences=[
                    SentencePair("Je suis un homme.", "I am a man."),
                    SentencePair("Tu es une femme.", "You are a woman."),
                    SentencePair("Le garçon et la fille.", "The boy and the girl."),
                    SentencePair("Je suis un garçon.", "I am a boy."),
                    SentencePair("La femme et l'homme.", "The woman and the man."),
                    SentencePair("Tu es un garçon.", "You are a boy."),
                    SentencePair("Je suis une fille.", "I am a girl."),
                    SentencePair("L'homme est grand.", "The man is tall."),
                ],
            ),
        ],
    ),
    UnitContent(
        title="Unit 2",
        description="Order food, count numbers",
        color_hex="#FF9600",
        skills=[
            SkillContent(
                title="Food",
                icon="apple",
                lesson_count=2,
                vocabulary=[
                    WordPair("la nourriture", "the food"),
                    WordPair("le petit-déjeuner", "breakfast"),
                    WordPair("le déjeuner", "lunch"),
                    WordPair("le dîner", "dinner"),
                    WordPair("le café", "the coffee"),
                    WordPair("l'eau", "the water"),
                    WordPair("le pain", "the bread"),
                    WordPair("la pomme", "the apple"),
                    WordPair("je veux", "I want"),
                    WordPair("tu veux", "you want"),
                ],
                sentences=[
                    SentencePair("Je veux le petit-déjeuner.", "I want breakfast."),
                    SentencePair("Tu veux du café?", "Do you want coffee?"),
                    SentencePair("Le dîner a du pain.", "Dinner has bread."),
                    SentencePair("Je mange une pomme.", "I eat an apple."),
                    SentencePair("Je bois de l'eau.", "I drink water."),
                    SentencePair("Le déjeuner est à midi.", "Lunch is at noon."),
                    SentencePair("Je veux la nourriture maintenant.", "I want the food now."),
                    SentencePair("Je bois du café le matin.", "I drink coffee in the morning."),
                ],
            ),
            SkillContent(
                title="Numbers",
                icon="hash",
                lesson_count=2,
                vocabulary=[
                    WordPair("un", "one"),
                    WordPair("deux", "two"),
                    WordPair("trois", "three"),
                    WordPair("quatre", "four"),
                    WordPair("cinq", "five"),
                    WordPair("six", "six"),
                    WordPair("sept", "seven"),
                    WordPair("huit", "eight"),
                    WordPair("neuf", "nine"),
                    WordPair("dix", "ten"),
                ],
                sentences=[
                    SentencePair("J'ai deux mains.", "I have two hands."),
                    SentencePair("Trois plus quatre font sept.", "Three plus four is seven."),
                    SentencePair("J'ai dix doigts.", "I have ten fingers."),
                    SentencePair("Elle a cinq pommes.", "She has five apples."),
                    SentencePair("Un, deux, trois.", "One, two, three."),
                    SentencePair("Il a six frères.", "He has six brothers."),
                    SentencePair("Neuf est presque dix.", "Nine is almost ten."),
                    SentencePair("J'ai huit ans.", "I am eight years old."),
                ],
            ),
        ],
    ),
]

FRENCH_COURSE = CourseContent(
    title="French",
    from_language="English",
    to_language="French",
    profile=FRENCH_PROFILE,
    units=FRENCH_UNITS,
)


COURSES: list[CourseContent] = [SPANISH_COURSE, FRENCH_COURSE]


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
