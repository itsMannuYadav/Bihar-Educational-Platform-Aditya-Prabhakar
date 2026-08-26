"""Seed the Bihar curriculum catalog (BSEB, Classes 6-10, all core subjects).

BSEB is NCERT-aligned. Every class/subject combination has a full chapter list
so the /catalog endpoints return real data for any demo selection.

Run with: uv run python -m app.db.seed_curriculum
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.curriculum import Board, Chapter, SchoolClass, Subject
from app.db.session import async_session_factory

CORE_SUBJECTS = ["Science", "Social Science", "Math", "Hindi", "English"]

# ---------------------------------------------------------------------------
# NCERT chapter lists — BSEB follows NCERT syllabus for Classes 6-10
# ---------------------------------------------------------------------------

CHAPTERS: dict[tuple[int, str], list[str]] = {
    # ── Class 6 ──────────────────────────────────────────────────────────────
    (6, "Science"): [
        "Food: Where Does It Come From?",
        "Components of Food",
        "Fibre to Fabric",
        "Sorting Materials into Groups",
        "Separation of Substances",
        "Changes Around Us",
        "Getting to Know Plants",
        "Body Movements",
        "The Living Organisms and Their Surroundings",
        "Motion and Measurement of Distances",
        "Light, Shadows and Reflection",
        "Electricity and Circuits",
        "Fun with Magnets",
        "Water",
        "Air Around Us",
        "Garbage In, Garbage Out",
    ],
    (6, "Math"): [
        "Knowing Our Numbers",
        "Whole Numbers",
        "Playing with Numbers",
        "Basic Geometrical Ideas",
        "Understanding Elementary Shapes",
        "Integers",
        "Fractions",
        "Decimals",
        "Data Handling",
        "Mensuration",
        "Algebra",
        "Ratio and Proportion",
        "Symmetry",
        "Practical Geometry",
    ],
    (6, "Social Science"): [
        "What, Where, How and When?",
        "On the Trail of the Earliest People",
        "From Gathering to Growing Food",
        "In the Earliest Cities",
        "What Books and Burials Tell Us",
        "Kingdoms, Kings and an Early Republic",
        "New Questions and Ideas",
        "Ashoka, the Emperor Who Gave Up War",
        "Vital Villages, Thriving Towns",
        "Traders, Kings and Pilgrims",
        "New Empires and Kingdoms",
        "Buildings, Paintings and Books",
        "Understanding Diversity",
        "Diversity and Discrimination",
        "What is Government?",
        "Key Elements of a Democratic Government",
        "Panchayati Raj",
        "Rural Administration",
        "Urban Administration",
        "Rural Livelihoods",
        "Urban Livelihoods",
        "The Earth in the Solar System",
        "Globe: Latitudes and Longitudes",
        "Motions of the Earth",
        "Maps",
        "Major Domains of the Earth",
        "Major Landforms of the Earth",
        "Our Country — India",
        "India: Climate, Vegetation and Wildlife",
    ],
    (6, "Hindi"): [
        "वह चिड़िया जो",
        "बचपन",
        "नादान दोस्त",
        "चाँद से थोड़ी सी गप्पें",
        "अक्षरों का महत्व",
        "पार नज़र के",
        "साथी हाथ बढ़ाना",
        "ऐसे–ऐसे",
        "टिकट-अलबम",
        "झाँसी की रानी",
        "जो देखकर भी नहीं देखते",
        "संसार पुस्तक है",
        "मैं सबसे छोटी होऊँ",
        "लोकगीत",
        "नौकर",
        "वन के मार्ग में",
        "साँस-साँस में बाँस",
    ],
    (6, "English"): [
        "Who Did Patrick's Homework?",
        "How the Dog Found Himself a New Master!",
        "Taro's Reward",
        "An Indian – American Woman in Space: Kalpana Chawla",
        "A Different Kind of School",
        "Who I Am",
        "Fair Play",
        "A Game of Chance",
        "Desert Animals",
        "The Banyan Tree",
    ],
    # ── Class 7 ──────────────────────────────────────────────────────────────
    (7, "Science"): [
        "Nutrition in Plants",
        "Nutrition in Animals",
        "Fibre to Fabric",
        "Heat",
        "Acids, Bases and Salts",
        "Physical and Chemical Changes",
        "Weather, Climate and Adaptations of Animals to Climate",
        "Winds, Storms and Cyclones",
        "Soil",
        "Respiration in Organisms",
        "Transportation in Animals and Plants",
        "Reproduction in Plants",
        "Motion and Time",
        "Electric Current and its Effects",
        "Light",
        "Water: A Precious Resource",
        "Forests: Our Lifeline",
        "Wastewater Story",
    ],
    (7, "Math"): [
        "Integers",
        "Fractions and Decimals",
        "Data Handling",
        "Simple Equations",
        "Lines and Angles",
        "The Triangle and its Properties",
        "Congruence of Triangles",
        "Comparing Quantities",
        "Rational Numbers",
        "Practical Geometry",
        "Perimeter and Area",
        "Algebraic Expressions",
        "Exponents and Powers",
        "Symmetry",
        "Visualising Solid Shapes",
    ],
    (7, "Social Science"): [
        "Tracing Changes Through a Thousand Years",
        "New Kings and Kingdoms",
        "The Delhi Sultans",
        "The Mughal Empire",
        "Rulers and Buildings",
        "Towns, Traders and Craftspersons",
        "Tribes, Nomads and Settled Communities",
        "Devotional Paths to the Divine",
        "The Making of Regional Cultures",
        "Eighteenth-Century Political Formations",
        "On Equality",
        "Role of the Government in Health",
        "How the State Government Works",
        "Growing up as Boys and Girls",
        "Women Change the World",
        "Understanding Media",
        "Understanding Advertising",
        "Markets Around Us",
        "A Shirt in the Market",
        "Environment",
        "Inside Our Earth",
        "Our Changing Earth",
        "Air",
        "Water",
        "Natural Vegetation and Wildlife",
        "Human Environment — Settlement, Transport and Communication",
        "Human Environment Interactions — The Tropical and the Subtropical Region",
        "Life in the Temperate Grasslands",
        "Life in the Deserts",
    ],
    (7, "Hindi"): [
        "हम पंछी उन्मुक्त गगन के",
        "दादी माँ",
        "हिमालय की बेटियाँ",
        "कठपुतली",
        "मिठाईवाला",
        "रक्त और हमारा शरीर",
        "पापा खो गए",
        "शाम – एक किसान",
        "चिड़िया की बच्ची",
        "अपूर्व अनुभव",
        "रहीम के दोहे",
        "कंचा",
        "एक तिनका",
        "खानपान की बदलती तस्वीर",
        "नीलकंठ",
        "भोर और बरखा",
        "वीर कुँवर सिंह",
        "संघर्ष के कारण मैं तुनुकमिज़ाज हो गया",
        "आश्रम का अनुमानित व्यय",
        "विप्लव-गायन",
    ],
    (7, "English"): [
        "Three Questions",
        "A Gift of Chappals",
        "Gopal and the Hilsa Fish",
        "The Ashes That Made Trees Bloom",
        "Quality",
        "Expert Detectives",
        "The Invention of Vita-Wonk",
        "Fire: Friend and Foe",
        "A Bicycle in Good Repair",
        "The Story of Cricket",
    ],
    # ── Class 8 ──────────────────────────────────────────────────────────────
    (8, "Science"): [
        "Crop Production and Management",
        "Microorganisms: Friend and Foe",
        "Synthetic Fibres and Plastics",
        "Materials: Metals and Non-Metals",
        "Coal and Petroleum",
        "Combustion and Flame",
        "Conservation of Plants and Animals",
        "Cell — Structure and Functions",
        "Reproduction in Animals",
        "Reaching the Age of Adolescence",
        "Force and Pressure",
        "Friction",
        "Sound",
        "Chemical Effects of Electric Current",
        "Some Natural Phenomena",
        "Light",
        "Stars and the Solar System",
        "Pollution of Air and Water",
    ],
    (8, "Math"): [
        "Rational Numbers",
        "Linear Equations in One Variable",
        "Understanding Quadrilaterals",
        "Practical Geometry",
        "Data Handling",
        "Squares and Square Roots",
        "Cubes and Cube Roots",
        "Comparing Quantities",
        "Algebraic Expressions and Identities",
        "Visualising Solid Shapes",
        "Mensuration",
        "Exponents and Powers",
        "Direct and Inverse Proportions",
        "Factorisation",
        "Introduction to Graphs",
        "Playing with Numbers",
    ],
    (8, "Social Science"): [
        "How, When and Where",
        "From Trade to Territory: The Company Establishes Power",
        "Ruling the Countryside",
        "Tribals, Dikus and the Vision of a Golden Age",
        "When People Rebel: 1857 and After",
        "Colonialism and the City",
        "Weavers, Iron Smelters and Factory Owners",
        "Civilising the 'Native', Educating the Nation",
        "Women, Caste and Reform",
        "The Changing World of Visual Arts",
        "The Making of the National Movement: 1870s–1947",
        "India After Independence",
        "The Indian Constitution",
        "Understanding Secularism",
        "Why Do We Need a Parliament?",
        "Understanding Laws",
        "Judiciary",
        "Understanding Our Criminal Justice System",
        "Understanding Marginalisation",
        "Confronting Marginalisation",
        "Public Facilities",
        "Law and Social Justice",
        "Resources",
        "Land, Soil, Water, Natural Vegetation and Wildlife Resources",
        "Mineral and Power Resources",
        "Agriculture",
        "Industries",
        "Human Resources",
    ],
    (8, "Hindi"): [
        "ध्वनि",
        "लाख की चूड़ियाँ",
        "बस की यात्रा",
        "दीवानों की हस्ती",
        "चिट्ठियों की अनूठी दुनिया",
        "भगवान के डाकिए",
        "क्या निराश हुआ जाए",
        "यह सबसे कठिन समय नहीं",
        "कबीर की साखियाँ",
        "कामचोर",
        "जब सिनेमा ने बोलना सीखा",
        "सुदामा चरित",
        "जहाँ पहिया है",
        "अकबरी लोटा",
        "सूरदास के पद",
        "पानी की कहानी",
        "बाज और साँप",
        "टोपी",
    ],
    (8, "English"): [
        "The Best Christmas Present in the World",
        "The Tsunami",
        "Glimpses of the Past",
        "Bepin Choudhury's Lapse of Memory",
        "The Summit Within",
        "This is Jody's Fawn",
        "A Visit to Cambridge",
        "A Short Monsoon Diary",
        "The Great Stone Face I",
        "The Great Stone Face II",
    ],
    # ── Class 9 ──────────────────────────────────────────────────────────────
    (9, "Science"): [
        "Matter in Our Surroundings",
        "Is Matter Around Us Pure?",
        "Atoms and Molecules",
        "Structure of the Atom",
        "The Fundamental Unit of Life",
        "Tissues",
        "Diversity in Living Organisms",
        "Motion",
        "Force and Laws of Motion",
        "Gravitation",
        "Work and Energy",
        "Sound",
        "Why Do We Fall Ill?",
        "Natural Resources",
        "Improvement in Food Resources",
    ],
    (9, "Math"): [
        "Number Systems",
        "Polynomials",
        "Coordinate Geometry",
        "Linear Equations in Two Variables",
        "Introduction to Euclid's Geometry",
        "Lines and Angles",
        "Triangles",
        "Quadrilaterals",
        "Areas of Parallelograms and Triangles",
        "Circles",
        "Constructions",
        "Heron's Formula",
        "Surface Areas and Volumes",
        "Statistics",
        "Probability",
    ],
    (9, "Social Science"): [
        "The French Revolution",
        "Socialism in Europe and the Russian Revolution",
        "Nazism and the Rise of Hitler",
        "Forest Society and Colonialism",
        "Pastoralists in the Modern World",
        "Peasants and Farmers",
        "History and Sport: The Story of Cricket",
        "Clothing: A Social History",
        "What is Democracy? Why Democracy?",
        "Constitutional Design",
        "Electoral Politics",
        "Working of Institutions",
        "Democratic Rights",
        "The Story of Village Palampur",
        "People as Resource",
        "Poverty as a Challenge",
        "Food Security in India",
        "India — Size and Location",
        "Physical Features of India",
        "Drainage",
        "Climate",
        "Natural Vegetation and Wildlife",
        "Population",
    ],
    (9, "Hindi"): [
        "दो बैलों की कथा",
        "ल्हासा की ओर",
        "उपभोक्तावाद की संस्कृति",
        "साँवले सपनों की याद",
        "नाना साहब की पुत्री देवी मैना को भस्म कर दिया गया",
        "प्रेमचंद के फटे जूते",
        "मेरे बचपन के दिन",
        "एक कुत्ता और एक मैना",
        "साखियाँ एवं सबद",
        "वाख",
        "सवैये",
        "कैदी और कोकिला",
        "ग्राम श्री",
        "चंद्र गहना से लौटती बेर",
        "मेघ आए",
        "यमराज की दिशा",
        "बच्चे काम पर जा रहे हैं",
    ],
    (9, "English"): [
        "The Fun They Had",
        "The Sound of Music",
        "The Little Girl",
        "A Truly Beautiful Mind",
        "The Snake and the Mirror",
        "My Childhood",
        "Packing",
        "Reach for the Top",
        "The Bond of Love",
        "Kathmandu",
        "If I Were You",
    ],
    # ── Class 10 ─────────────────────────────────────────────────────────────
    (10, "Science"): [
        "Chemical Reactions and Equations",
        "Acids, Bases and Salts",
        "Metals and Non-metals",
        "Carbon and its Compounds",
        "Periodic Classification of Elements",
        "Life Processes",
        "Control and Coordination",
        "How do Organisms Reproduce?",
        "Heredity and Evolution",
        "Light — Reflection and Refraction",
        "Human Eye and the Colourful World",
        "Electricity",
        "Magnetic Effects of Electric Current",
        "Sources of Energy",
        "Our Environment",
        "Management of Natural Resources",
    ],
    (10, "Math"): [
        "Real Numbers",
        "Polynomials",
        "Pair of Linear Equations in Two Variables",
        "Quadratic Equations",
        "Arithmetic Progressions",
        "Triangles",
        "Coordinate Geometry",
        "Introduction to Trigonometry",
        "Some Applications of Trigonometry",
        "Circles",
        "Constructions",
        "Areas Related to Circles",
        "Surface Areas and Volumes",
        "Statistics",
        "Probability",
    ],
    (10, "Social Science"): [
        "The Rise of Nationalism in Europe",
        "Nationalism in India",
        "The Making of a Global World",
        "The Age of Industrialisation",
        "Print Culture and the Modern World",
        "Development",
        "Sectors of the Indian Economy",
        "Money and Credit",
        "Globalisation and the Indian Economy",
        "Consumer Rights",
        "Power Sharing",
        "Federalism",
        "Democracy and Diversity",
        "Gender, Religion and Caste",
        "Popular Struggles and Movements",
        "Political Parties",
        "Outcomes of Democracy",
        "Challenges to Democracy",
        "Resources and Development",
        "Forest and Wildlife Resources",
        "Water Resources",
        "Agriculture",
        "Minerals and Energy Resources",
        "Manufacturing Industries",
        "Life Lines of National Economy",
    ],
    (10, "Hindi"): [
        "सूरदास के पद",
        "राम-लक्ष्मण-परशुराम संवाद",
        "सवैया और कवित्त",
        "आत्मकथ्य",
        "उत्साह और अट नहीं रही",
        "यह दंतुरित मुसकान और फसल",
        "छाया मत छूना",
        "कन्यादान",
        "संगतकार",
        "नेताजी का चश्मा",
        "बालगोबिन भगत",
        "लखनवी अंदाज़",
        "मानवीय करुणा की दिव्य चमक",
        "एक कहानी यह भी",
        "स्त्री शिक्षा के विरोधी कुतर्कों का खंडन",
        "नौबतखाने में इबादत",
        "संस्कृति",
        "माता का अँचल",
        "जॉर्ज पंचम की नाक",
        "साना-साना हाथ जोड़ि",
        "एही ठैयाँ झुलनी हेरानी हो रामा!",
        "मैं क्यों लिखता हूँ?",
    ],
    (10, "English"): [
        "A Letter to God",
        "Nelson Mandela: Long Walk to Freedom",
        "Two Stories about Flying",
        "From the Diary of Anne Frank",
        "Glimpses of India",
        "Mijbil the Otter",
        "Madam Rides the Bus",
        "The Sermon at Benares",
        "The Proposal",
        "A Tiger in the Zoo",
        "How to Tell Wild Animals",
        "The Ball Poem",
        "Amanda!",
        "Animals",
        "The Trees",
        "Fog",
        "The Tale of Custard the Dragon",
        "For Anne Gregory",
    ],
}


async def _get_or_create_board(db: AsyncSession) -> Board:
    board = (await db.execute(select(Board).where(Board.name == "BSEB"))).scalar_one_or_none()
    if board is None:
        board = Board(name="BSEB", state="Bihar")
        db.add(board)
        await db.flush()
    return board


async def seed_curriculum() -> None:
    async with async_session_factory() as db:
        board = await _get_or_create_board(db)

        # ── Ensure all Classes 6-10 exist ───────────────────────────────────
        existing_classes = {
            c.grade: c
            for c in (await db.execute(select(SchoolClass).where(SchoolClass.board_id == board.id)))
            .scalars()
            .all()
        }
        classes_by_grade: dict[int, SchoolClass] = dict(existing_classes)
        for grade in range(6, 11):
            if grade not in classes_by_grade:
                school_class = SchoolClass(
                    board_id=board.id, grade=grade, display_name=f"Class {grade}"
                )
                db.add(school_class)
                classes_by_grade[grade] = school_class
        await db.flush()

        # ── Ensure all Subjects exist ────────────────────────────────────────
        existing_subjects: set[tuple[int, str]] = {
            (s.class_id, s.name)
            for s in (
                await db.execute(
                    select(Subject).where(
                        Subject.class_id.in_(c.id for c in classes_by_grade.values())
                    )
                )
            )
            .scalars()
            .all()
        }
        subjects_by_key: dict[tuple[int, str], Subject] = {}
        for grade, school_class in classes_by_grade.items():
            for subject_name in CORE_SUBJECTS:
                key = (school_class.id, subject_name)
                if key not in existing_subjects:
                    subject = Subject(class_id=school_class.id, name=subject_name)
                    db.add(subject)
                    subjects_by_key[(grade, subject_name)] = subject
        await db.flush()

        # Build a lookup: (grade, subject_name) → Subject ORM object
        all_subjects_result = (
            (
                await db.execute(
                    select(Subject).where(
                        Subject.class_id.in_(c.id for c in classes_by_grade.values())
                    )
                )
            )
            .scalars()
            .all()
        )
        grade_for_class: dict[int, int] = {sc.id: g for g, sc in classes_by_grade.items()}
        subject_lookup: dict[tuple[int, str], Subject] = {
            (grade_for_class[s.class_id], s.name): s for s in all_subjects_result
        }

        # ── Seed chapters ────────────────────────────────────────────────────
        chapters_added = 0
        for (grade, subject_name), chapter_list in CHAPTERS.items():
            subject = subject_lookup.get((grade, subject_name))
            if subject is None:
                continue

            existing_names = {
                name
                for (name,) in (
                    await db.execute(select(Chapter.name).where(Chapter.subject_id == subject.id))
                ).all()
            }
            for seq, chapter_name in enumerate(chapter_list, start=1):
                if chapter_name not in existing_names:
                    db.add(
                        Chapter(
                            subject_id=subject.id,
                            name=chapter_name,
                            sequence_no=seq,
                        )
                    )
                    chapters_added += 1

        await db.commit()
        total_chapters = sum(len(v) for v in CHAPTERS.values())
        print(
            f"Seeded curriculum: board={board.name}, "
            f"classes=5 (6-10), subjects={len(CORE_SUBJECTS)}, "
            f"chapters_in_seed={total_chapters}, chapters_added={chapters_added}"
        )


if __name__ == "__main__":
    asyncio.run(seed_curriculum())
