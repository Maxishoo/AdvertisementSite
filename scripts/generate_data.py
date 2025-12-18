import asyncio
import os
import random

from dotenv import load_dotenv
from faker import Faker
from asyncpg import create_pool, Pool


load_dotenv()
fake = Faker('ru_RU')

CATEGORIES = [
    ("Электроника", "elektronika", "/icons/elektronika.png", "Товары для дома и офиса"),
    ("Недвижимость", "nedvizhimost",
     "/icons/nedvizhimost.png", "Квартиры, дома, земля"),
    ("Авто", "avto", "/icons/avto.png", "Автомобили и запчасти"),
    ("Работа", "rabota", "/icons/rabota.png", "Вакансии и резюме"),
    ("Услуги", "uslugi", "/icons/uslugi.png", "Бытовые и профессиональные услуги"),
    ("Мода и стиль", "moda", "/icons/moda.png", "Одежда, обувь и аксессуары"),
    ("Детские товары", "detskie-tovary",
     "/icons/detskie-tovary.png", "Всё для детей и родителей"),
    ("Дом и сад", "dom-i-sad", "/icons/dom-i-sad.png",
     "Мебель, инструменты, растения"),
    ("Зоотовары", "zootovary", "/icons/zootovary.png", "Всё для животных"),
    ("Хобби и отдых", "hobbi", "/icons/hobbi.png",
     "Книги, музыка, спорт, коллекции"),
    ("Бытовая техника", "bitovaya-tehnika", "/icons/bitovaya-tehnika.png",
     "Холодильники, стиральные машины и др."),
    ("Стройматериалы", "stroymaterialy",
     "/icons/stroymaterialy.png", "Всё для ремонта и строительства"),
    ("Антиквариат и искусство", "antikvariat",
     "/icons/antikvariat.png", "Раритеты, картины, скульптуры"),
    ("Красота и здоровье", "krasota", "/icons/krasota.png",
     "Косметика, парфюмерия, медтехника"),
    ("Спорт и туризм", "sport", "/icons/sport.png",
     "Инвентарь, экипировка, путешествия"),
    ("Музыкальные инструменты", "muzyka",
     "/icons/muzyka.png", "Гитары, синтезаторы, усилители"),
    ("Игры и приставки", "igry", "/icons/igry.png", "Консоли, диски, аксессуары"),
    ("Фото и видео", "foto-video", "/icons/foto-video.png",
     "Камеры, объективы, штативы"),
    ("Компьютеры", "kompyutery", "/icons/kompyutery.png",
     "ПК, ноутбуки, комплектующие"),
    ("Телефоны", "telefony", "/icons/telefony.png",
     "Смартфоны, аксессуары, запчасти"),
    ("Книги", "knigi", "/icons/knigi.png",
     "Художественная и техническая литература"),
    ("Сельхозтехника", "selskhoztehnika",
     "/icons/selskhoztehnika.png", "Тракторы, культиваторы, запчасти"),
    ("Гараж", "garazh", "/icons/garazh.png",
     "Инструменты, запчасти, оборудование"),
    ("Билеты и путешествия", "bilety",
     "/icons/bilety.png", "Концерты, авиа, ж/д билеты"),
    ("Бизнес", "biznes", "/icons/biznes.png",
     "Готовый бизнес, оборудование, франшизы"),
    ("Продукты питания", "produkty", "/icons/produkty.png",
     "Свежие, домашние, фермерские товары"),
    ("Оборудование", "oborudovanie", "/icons/oborudovanie.png",
     "Промышленное и торговое оборудование"),
    ("Сырьё", "syrje", "/icons/syrje.png", "Металл, пластик, древесина и др."),
    ("Инвестиции", "investicii", "/icons/investicii.png",
     "Ценные бумаги, драгметаллы, ПИФы"),
    ("Автосервис", "avtoservis", "/icons/avtoservis.png",
     "Ремонт, шиномонтаж, эвакуация"),
    ("Перевозки", "perevozki", "/icons/perevozki.png",
     "Грузоперевозки, грузчики, такси"),
    ("Ремонт и строительство", "remont",
     "/icons/remont.png", "Мастера на дом, дизайн, отделка"),
    ("Образование", "obrazovanie", "/icons/obrazovanie.png",
     "Репетиторы, курсы, подготовка"),
    ("Финансы", "finansy", "/icons/finansy.png",
     "Кредиты, страхование, бухгалтерия"),
    ("Реклама и маркетинг", "reklama",
     "/icons/reklama.png", "Продвижение, полиграфия, SMM"),
    ("Юридические услуги", "urist", "/icons/urist.png",
     "Консультации, документы, суды"),
    ("Медицинские услуги", "medicina",
     "/icons/medicina.png", "Анализы, врачи, стоматология"),
    ("Развлечения", "razvlecheniya", "/icons/razvlecheniya.png",
     "Квесты, аниматоры, праздники"),
    ("Одежда", "odezhda", "/icons/odezhda.png",
     "Мужская, женская и детская одежда"),
    ("Обувь", "obuv", "/icons/obuv.png", "Кроссовки, туфли, сапоги и т.д."),
    ("Сумки и чемоданы", "sumki", "/icons/sumki.png",
     "Рюкзаки, клатчи, дорожные сумки"),
    ("Ювелирные изделия", "yuvelirka",
     "/icons/yuvelirka.png", "Золото, серебро, бриллианты"),
    ("Часы", "chasy", "/icons/chasy.png", "Наручные, настенные, антикварные"),
    ("Велосипеды", "velosipedy", "/icons/velosipedy.png",
     "Горные, детские, электровелосипеды"),
    ("Мото", "moto", "/icons/moto.png", "Мотоциклы, скутеры, экипировка"),
    ("Лодки и водный транспорт", "lodka",
     "/icons/lodka.png", "Катера, моторы, снаряжение"),
    ("Авиамоделизм", "aviamodelizm", "/icons/aviamodelizm.png",
     "Дроны, квадрокоптеры, радиоуправление"),
    ("Коллекционирование", "kollekcionirovanie",
     "/icons/kollekcionirovanie.png", "Монеты, марки, фигурки"),
    ("Посуда и кухня", "posuda", "/icons/posuda.png",
     "Кастрюли, столовые приборы, техника"),
    ("Интерьер", "interer", "/icons/interer.png",
     "Шторы, картины, декор, освещение"),
    ("Товары для офиса", "ofis", "/icons/ofis.png", "Мебель, оргтехника, канцелярия"),
    ("Свадьба", "svadba", "/icons/svadba.png", "Платья, костюмы, оформление"),
    ("Подарки", "podarki", "/icons/podarki.png", "Сувениры, гаджеты, упаковка"),
    ("Химия и удобрения", "himiya", "/icons/himiya.png",
     "Агрохимия, бытовая химия, реактивы"),
    ("Полиграфия", "poligrafiya", "/icons/poligrafiya.png",
     "Печать, этикетки, упаковка"),
    ("Канцелярия", "kancelyariya",
     "/icons/kancelyariya.png", "Ручки, блокноты, скрепки"),
    ("Аудиотехника", "audio", "/icons/audio.png", "Наушники, колонки, усилители"),
    ("Видео и ТВ", "video-tv", "/icons/video-tv.png",
     "Телевизоры, приставки, проекторы"),
    ("Климатическая техника", "klimat", "/icons/klimat.png",
     "Кондиционеры, обогреватели, вентиляторы"),
    ("Инструменты", "instrumenty", "/icons/instrumenty.png",
     "Ручные и электроинструменты"),
    ("Автоэлектроника", "avtoelektronika",
     "/icons/avtoelektronika.png", "Магнитолы, камеры, сигнализации"),
    ("Шины и диски", "shiny", "/icons/shiny.png", "Летняя, зимняя, кованые диски"),
    ("Мебель", "mebel", "/icons/mebel.png", "Корпусная, мягкая, офисная мебель"),
    ("Двери и окна", "dveri-okna", "/icons/dveri-okna.png",
     "Межкомнатные, входные, остекление"),
    ("Сантехника", "santehnika", "/icons/santehnika.png", "Смесители, ванны, трубы"),
    ("Электрика", "elektrika", "/icons/elektrika.png", "Розетки, автоматы, кабели"),
    ("Освещение", "osveshchenie", "/icons/osveshchenie.png",
     "Люстры, лампы, светодиоды"),
    ("Текстиль", "tekstil", "/icons/tekstil.png",
     "Постельное бельё, покрывала, ковры"),
    ("Сад и огород", "sad-ogorod", "/icons/sad-ogorod.png",
     "Семена, рассада, садовый инвентарь"),
    ("Растения", "rasteniya", "/icons/rasteniya.png",
     "Цветы, деревья, комнатные растения"),
    ("Аквариумистика", "akvariumistika",
     "/icons/akvariumistika.png", "Аквариумы, рыбки, оборудование"),
    ("Товары для животных", "tovary-dlya-zhivotnyh",
     "/icons/tovary-dlya-zhivotnyh.png", "Корма, клетки, лежаки"),
    ("Ветеринария", "veterinariya", "/icons/veterinariya.png",
     "Клиники, лекарства, анализы"),
    ("Диеты и питание", "diety-pitanie", "/icons/diety-pitanie.png",
     "БАДы, протеины, специальные продукты"),
    ("Спортивное питание", "sportivnoe-pitanie",
     "/icons/sportivnoe-pitanie.png", "Протеин, гейнеры, аминокислоты"),
    ("Фитнес", "fitnes", "/icons/fitnes.png",
     "Тренажёры, абонементы, инструкторы"),
    ("Йога и медитация", "yoga", "/icons/yoga.png", "Коврики, одежда, занятия"),
    ("Охота и рыбалка", "ohota-rybalka",
     "/icons/ohota-rybalka.png", "Снасти, оружие, экипировка"),
    ("Туризм", "turizm", "/icons/turizm.png", "Палатки, рюкзаки, навигаторы"),
    ("Кемпинг", "kemping", "/icons/kemping.png", "Спальные мешки, мангалы, посуда"),
    ("Экстрим", "ekstrim", "/icons/ekstrim.png", "Парашюты, скейтборды, защита"),
    ("Кино и театр", "kino-teatr", "/icons/kino-teatr.png",
     "Билеты, сувениры, актёрские услуги"),
    ("Музыка", "muzyka-2", "/icons/muzyka-2.png", "Концерты, студии, обучение"),
    ("Искусство", "iskusstvo", "/icons/iskusstvo.png",
     "Выставки, картины, скульптуры"),
    ("Фотографы", "fotografi", "/icons/fotografi.png", "Съёмка, ретушь, студии"),
    ("Видеосъёмка", "videosyomka", "/icons/videosyomka.png", "Свадьбы, события, монтаж"),
    ("Дизайн", "dizain", "/icons/dizain.png", "Графика, интерьер, логотипы"),
    ("Программирование", "programmirovanie",
     "/icons/programmirovanie.png", "Разработка сайтов и приложений"),
    ("Переводы", "perevody", "/icons/perevody.png", "Письменные и устные переводы"),
    ("Копирайтинг", "kopiraiting", "/icons/kopiraiting.png", "Тексты, статьи, SEO"),
    ("Курьерские услуги", "kurer", "/icons/kurer.png",
     "Доставка, курьеры, экспресс-почта"),
    ("Уборка", "uborka", "/icons/uborka.png", "Клининг, химчистка, стирка"),
]

TAGS = [
    ("б/у", "b_u"),
    ("новый", "novyj"),
    ("срочная продажа", "srochnaya-prodazha"),
    ("для бизнеса", "dlya-biznesa"),
    ("торг", "torg"),
    ("без торга", "bez-torga"),
    ("возможен обмен", "vozmozhen-obmen"),
    ("цена снижена", "cena-snizhena"),
    ("в наличии", "v-nalichii"),
    ("под заказ", "pod-zakaz"),
    ("доставка", "dostavka"),
    ("самовывоз", "samovyvoz"),
    ("с фото", "s-foto"),
    ("без фото", "bez-foto"),
    ("проверенный продавец", "proverennyy-prodavets"),
    ("частное лицо", "chastnoe-litso"),
    ("магазин", "magazin"),
    ("оригинал", "original"),
    ("не оригинал", "ne-original"),
    ("гарантия", "garantiya"),
    ("без гарантии", "bez-garantii"),
    ("в коробке", "v-korobke"),
    ("без коробки", "bez-korobki"),
    ("как новый", "kak-novyy"),
    ("идеальное состояние", "idealnoe-sostoyanie"),
    ("хорошее состояние", "horoshee-sostoyanie"),
    ("удовлетворительное состояние", "udovletvoritelnoe-sostoyanie"),
    ("требует ремонта", "trebuet-remonta"),
    ("неисправен", "neispraven"),
    ("редкий", "redkiy"),
    ("коллекционный", "kollektsionnyy"),
    ("лимитированная серия", "limitirovannaya-seriya"),
    ("распродажа", "rassprozha"),
    ("акция", "aktsiya"),
    ("скидка", "skidka"),
    ("бесплатно", "besplatno"),
    ("отказ от покупки", "otkaz-ot-pokupki"),
    ("лишнее", "lishnee"),
    ("не пригодилось", "ne-prigodilos"),
    ("переезд", "pereezd"),
    ("ликвидация", "likvidatsiya"),
    ("для подарка", "dlya-podarka"),
    ("для начинающих", "dlya-nachinayushchih"),
    ("для профессионалов", "dlya-professionalov"),
    ("для детей", "dlya-detey"),
    ("для взрослых", "dlya-vzroslyh"),
    ("для пожилых", "dlya-pozhilyh"),
    ("для школы", "dlya-shkoly"),
    ("для университета", "dlya-universiteta"),
    ("для офиса", "dlya-ofisa"),
    ("для дома", "dlya-doma"),
    ("для дачи", "dlya-dachi"),
    ("для гаража", "dlya-garazha"),
    ("для автомобиля", "dlya-avtomobilya"),
    ("для кухни", "dlya-kuhni"),
    ("для ванной", "dlya-vannoy"),
    ("для спальни", "dlya-spalni"),
    ("для гостиной", "dlya-gostinoy"),
    ("для сада", "dlya-sada"),
    ("для огорода", "dlya-ogoroda"),
    ("для животных", "dlya-zhivotnyh"),
    ("для кошек", "dlya-koshek"),
    ("для собак", "dlya-sobak"),
    ("для птиц", "dlya-ptic"),
    ("для рыб", "dlya-ryb"),
    ("эко", "eko"),
    ("ручной работы", "ruchnoy-raboty"),
    ("сделано вручную", "sdelano-vruchnuyu"),
    ("в комплекте", "v-komplekte"),
    ("без аксессуаров", "bez-aksessuarov"),
    ("полный комплект", "polnyy-komplekt"),
    ("оригинальная упаковка", "originalnaya-upakovka"),
    ("батарейки в комплекте", "batareyki-v-komplekte"),
    ("зарядное устройство в комплекте", "zarjadnoe-ustroystvo-v-komplekte"),
    ("инструкция", "instruktsiya"),
    ("на гарантии", "na-garantii"),
    ("после гарантии", "posle-garantii"),
    ("запечатан", "zapechatan"),
    ("вскрыт", "vskryt"),
    ("в рабочем состоянии", "v-rabochom-sostoyanii"),
    ("после ремонта", "posle-remonta"),
    ("реставрирован", "restavrirovan"),
    ("антиквариат", "antikvariat"),
    ("советский", "sovetskiy"),
    ("ретро", "retro"),
    ("современный", "sovremennyy"),
    ("минимализм", "minimalizm"),
    ("хай-тек", "hay-tek"),
    ("в стиле лофт", "v-stile-loft"),
    ("в стиле прованс", "v-stile-provans"),
    ("элитный", "elitnyy"),
    ("премиум", "premium"),
    ("эконом", "ekonom"),
    ("дешево", "deshevo"),
    ("дорого", "dorogo"),
    ("выгодно", "vygodno"),
    ("только сегодня", "tolko-segodnya"),
    ("до конца недели", "do-konca-nedeli"),
    ("до конца месяца", "do-konca-mesyaca"),
    ("новинка", "novinka"),
    ("популярный", "populyarnyy"),
    ("хит продаж", "hit-prodazh"),
    ("востребованный", "vostrebovannyy"),
    ("редко встречается", "redko-vstrechaetsya"),
    ("в единственном экземпляре", "v-edinstvennom-ekzemple"),
    ("можно забрать сегодня", "mozhno-zabrat-segodnya"),
]

CITY_DISTRICTS = {
    "Москва": [
        "Центральный", "Северный", "Восточный", "Южный", "Западный",
        "Таганский", "Арбат", "Кузьминки", "Солнцево", "Зеленоград"
    ],
    "Санкт-Петербург": [
        "Адмиралтейский", "Василеостровский", "Петроградский", "Московский",
        "Невский", "Кировский", "Калининский", "Приморский", "Фрунзенский"
    ],
    "Новосибирск": [
        "Центральный", "Железнодорожный", "Ленинский", "Октябрьский", "Дзержинский"
    ],
    "Екатеринбург": [
        "Верх-Исетский", "Железнодорожный", "Кировский", "Ленинский", "Октябрьский"
    ],
    "Казань": [
        "Вахитовский", "Приволжский", "Советский", "Московский", "Ново-Савиновский"
    ],
    "Нижний Новгород": [
        "Нижегородский", "Приокский", "Советский", "Ленинский", "Автозаводский"
    ],
    "Челябинск": [
        "Калининский", "Ленинский", "Металлургический", "Тракторозаводский", "Центральный"
    ],
    "Самара": [
        "Железнодорожный", "Кировский", "Ленинский", "Октябрьский", "Советский"
    ],
    "Омск": [
        "Центральный", "Ленинский", "Советский", "Кировский", "Октябрьский"
    ],
    "Ростов-на-Дону": [
        "Железнодорожный", "Ленинский", "Октябрьский", "Пролетарский", "Советский"
    ]
}

PRODUCT_TEMPLATES = {
    "Электроника": [
        ("iPhone 13", "Смартфон Apple iPhone 13, 128GB, синий"),
        ("Samsung Galaxy S22", "Смартфон Samsung Galaxy S22, 256GB, черный"),
        ("MacBook Pro 14\"", "Ноутбук Apple MacBook Pro 14\", M1 Pro, 16GB RAM"),
        ("Sony WH-1000XM5", "Наушники Sony WH-1000XM5, шумоподавление"),
        ("iPad Air 5", "Планшет Apple iPad Air 5, 256GB, серый"),
    ],
    "Авто": [
        ("Toyota Camry", "Седан Toyota Camry, 2020 г., пробег 45 000 км"),
        ("BMW X5", "Внедорожник BMW X5, 2021 г., полный привод"),
        ("Lada Granta", "Седан Lada Granta, 2022 г., 1.6 л, механика"),
        ("KIA Rio", "Хэтчбек KIA Rio, 2019 г., автомат, кожаный салон"),
        ("Volkswagen Polo", "Седан Volkswagen Polo, 2023 г., мультимедиа"),
    ],
    "Недвижимость": [
        ("Квартира в новостройке", "2-комнатная квартира, 55 м², ЖК \"Солнечный\""),
        ("Комната в центре", "Отдельная комната в 3-комнатной квартире, 18 м²"),
        ("Частный дом", "Дом 120 м² на участке 6 соток, с ремонтом"),
        ("Гараж", "Гараж в ГСК \"Автодром\", 6х4 м, кирпич"),
        ("Офисное помещение", "Офис 45 м² в бизнес-центре, отдельный вход"),
    ],
    "Мода и стиль": [
        ("Пальто Max Mara", "Женское пальто Max Mara, размер 44, кашемир"),
        ("Кроссовки Nike", "Мужские кроссовки Nike Air Max, размер 43, черные"),
        ("Сумка Louis Vuitton", "Женская сумка Louis Vuitton Neverfull MM"),
        ("Часы Rolex", "Мужские часы Rolex Submariner, сталь"),
        ("Кожаная куртка", "Мужская куртка из натуральной кожи, размер L"),
    ],
    "Детские товары": [
        ("Коляска Baby Jogger", "Прогулочная коляска Baby Jogger City Mini GT2"),
        ("Конструктор Lego", "Набор Lego Technic Porsche 911, 1470 деталей"),
        ("Школьный рюкзак", "Рюкзак для школьника с ортопедической спинкой"),
        ("Детская кроватка", "Деревянная кроватка-манеж \"Малыш\", с матрасом"),
        ("Игровая приставка", "Приставка Nintendo Switch OLED с играми"),
    ],
    "Хобби и отдых": [
        ("Велосипед Stels", "Горный велосипед Stels Navigator 950, 29\""),
        ("Рыболовные снасти", "Набор для спиннинговой рыбалки: удилище, катушка"),
        ("Настольная игра", "Монополия \"Москва\", подарочное издание"),
        ("Билет на концерт", "2 билета на концерт Басты в Крокус Сити Холл"),
        ("Палатка", "Туристическая палатка Alexika Montana 3, 3-местная"),
    ]
}

DESCRIPTION_TEMPLATES = {
    "Электроника": [
        "Куплен в {store} в {year}. Все аксессуары в комплекте: коробка, зарядка, документы. Состояние отличное, без царапин. Продаю, потому что купил новую модель.",
        "Гарантия до {warranty_end}. Использовался аккуратно, только в чехле. Полный комплект с аксессуарами. Возможен торг при осмотре.",
        "Покупал для работы, но не подошел формат. Работает исправно, батарея держит заряд хорошо. Отдам вместе с чехлом и защитным стеклом."
    ],
    "Авто": [
        "Оригинал ПТС, 1 собственник. Машина в идеальном состоянии, не битая, не крашеная. Полный комплект: два ключа, инструменты, аптечка. Регулярное ТО у дилера.",
        "Пробег реальный, подтвержден сервисной историей. Салон в хорошем состоянии, кондиционер работает отлично. Возможен тест-драйв для серьезных покупателей.",
        "Авто в семейной эксплуатации, хранится в теплом гараже. Дополнительно установлены: магнитола, камера заднего вида, коврики. Все расходники менялись вовремя."
    ],
    "Недвижимость": [
        "Квартира в новом доме с современной отделкой. Большие окна, раздельный санузел, балкон застеклен. Рядом школа, детский сад, магазины. Ипотека одобрена.",
        "Хороший район, тихий двор, рядом парк. После косметического ремонта, можно заезжать и жить. Остается встроенная кухня и кондиционер.",
        "Участок правильной формы, электричество подведено. Рядом лес и озеро. Идеально для строительства загородного дома или дачи."
    ],
    "default": [
        "Товар в отличном состоянии. Куплен недавно, но не пригодился. Все аксессуары на месте. Возможен торг при самовывозе.",
        "Продается в связи с переездом. Состояние как новое, использовался аккуратно. Гарантия еще действует до конца года.",
        "Полный комплект с документами. Никаких сколов или царапин. Отличный вариант для подарка или личного использования."
    ]
}

PRICE_RANGES = {
    "Электроника": (5000, 300000),
    "Авто": (300000, 5000000),
    "Недвижимость": (2000000, 50000000),
    "Мода и стиль": (1000, 500000),
    "Детские товары": (500, 100000),
    "Хобби и отдых": (1000, 500000),
    "default": (1000, 50000)
}


async def generate_categories(pool: Pool):
    async with pool.acquire() as conn:
        for name, slug, icon, desc in CATEGORIES:
            await conn.execute("""
                INSERT INTO categories (name, slug, icon_url, description)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (name) DO NOTHING
            """, name, slug, icon, desc)
    print("Категории загружены")


async def generate_tags(pool: Pool):
    async with pool.acquire() as conn:
        for name, slug in TAGS:
            await conn.execute("""
                INSERT INTO tags (name, slug)
                VALUES ($1, $2)
                ON CONFLICT (name) DO NOTHING
            """, name, slug)
    print("Теги загружены")


async def generate_users(pool: Pool, count: int = 100):
    admin_email = "admin@avito.ru"
    admin_phone = "+74951234567"

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (email, phone, password_hash, username, first_name, last_name, role, is_verified)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (email) DO NOTHING
        """, admin_email, admin_phone, "admin_hash", "admin", "Администратор", "Системы", "admin", True)

        for i in range(1, 6):
            await conn.execute("""
                INSERT INTO users (email, phone, password_hash, username, first_name, last_name, role, is_verified)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                               f"moderator{i}@avito.ru",
                               f"+7916111223{i}",
                               f"mod_hash_{i}",
                               f"moderator_{i}",
                               fake.first_name_male(),
                               fake.last_name_male(),
                               "moderator",
                               True
                               )

        for i in range(count):
            if random.random() > 0.7:
                email = f"{fake.user_name().lower()}{random.randint(10, 99)}@mail.ru"
            else:
                email = fake.email()

            phone = f"+7{random.choice(['903', '916', '925', '985'])}{fake.numerify('#######')}"
            username = f"user_{fake.user_name().lower()}{i}"
            first_name = fake.first_name()
            last_name = fake.last_name()

            await conn.execute("""
                INSERT INTO users (email, phone, password_hash, username, first_name, last_name, role, is_verified)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                               email, phone, "user_hash_stub",
                               username[:128], first_name, last_name,
                               "user", random.random() > 0.1
                               )
    print(f"Пользователи ({count}) загружены")


async def generate_locations(pool: Pool, count: int = 50):
    async with pool.acquire() as conn:
        inserted = 0
        while inserted < count:
            city = random.choice(list(CITY_DISTRICTS.keys()))
            district = random.choice(CITY_DISTRICTS[city])
            street = fake.street_name()
            building = str(fake.building_number())

            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM locations 
                    WHERE city = $1 AND district = $2 AND street = $3 AND building = $4
                )
            """, city, district, street, building)

            if exists:
                continue

            moscow_coords = (55.7558, 37.6173)
            spb_coords = (59.9343, 30.3351)

            if city == "Москва":
                lat = moscow_coords[0] + random.uniform(-0.1, 0.1)
                lon = moscow_coords[1] + random.uniform(-0.1, 0.1)
            elif city == "Санкт-Петербург":
                lat = spb_coords[0] + random.uniform(-0.1, 0.1)
                lon = spb_coords[1] + random.uniform(-0.1, 0.1)
            else:
                lat = float(fake.latitude())
                lon = float(fake.longitude())

            postal_code = f"1{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"

            await conn.execute("""
                INSERT INTO locations (city, district, street, building, latitude, longitude, postal_code)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (city, district, street, building) DO NOTHING
            """, city, district, street, building, lat, lon, postal_code)

            inserted += 1
    print(f"Локации ({count}) загружены")


async def generate_ads(pool: Pool, count: int = 150):
    async with pool.acquire() as conn:
        user_ids = [r['id'] for r in await conn.fetch("SELECT id FROM users WHERE role = 'user'")]
        category_ids = {r['name']: r['id'] for r in await conn.fetch("SELECT id, name FROM categories")}
        location_ids = [r['id'] for r in await conn.fetch("SELECT id FROM locations")]

        tag_ids = {r['name']: r['id'] for r in await conn.fetch("SELECT id, name FROM tags")}

        for i in range(count):
            category_name = random.choices(
                list(PRODUCT_TEMPLATES.keys()),
                weights=[5, 3, 3, 2, 2, 1],
                k=1
            )[0]

            category_id = category_ids.get(category_name)
            if not category_id:
                continue

            product_name, product_desc = random.choice(
                PRODUCT_TEMPLATES[category_name])

            conditions = ["в отличном состоянии",
                          "после гарантии", "с гарантией", "новый"]
            title = f"{product_name} {random.choice(conditions)}"
            if random.random() > 0.7:
                title += f" - {random.randint(50, 90)}% цены"

            templates = DESCRIPTION_TEMPLATES.get(
                category_name, DESCRIPTION_TEMPLATES["default"])
            template = random.choice(templates)

            description = template.format(
                store=random.choice(
                    ["М.Видео", "Ситилинк", "DNS", "автосалон \"Москва\"", "ИКЕА", "Ламода"]),
                year=random.randint(2018, 2023),
                warranty_end=f"{random.randint(2024, 2026)} года",
                city=random.choice(list(CITY_DISTRICTS.keys()))
            )

            if category_name == "Авто":
                description += f"\n\nДополнительно: {random.choice(['все документы в порядке', 'полный комплект ключей', 'машина не в кредите'])}"
            elif category_name == "Недвижимость":
                description += f"\n\nИнфраструктура: {random.choice(['рядом метро', 'школа и детсад в 5 минутах', 'парковка во дворе'])}"

            min_price, max_price = PRICE_RANGES.get(
                category_name, PRICE_RANGES["default"])
            price = round(random.uniform(min_price, max_price), -3)

            user_id = random.choice(user_ids)
            location_id = random.choice(location_ids)
            currency = "RUB"
            status = "APPROVED" if random.random() > 0.05 else "PENDING"
            is_active = status == "APPROVED"

            # Вставляем объявление
            ad_id = await conn.fetchval("""
                INSERT INTO ads (
                    user_id, category_id, location_id, title, description,
                    price, currency, moderation_status, is_active, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW() - (INTERVAL '1 hour' * $10))
                RETURNING id
            """,
                                        user_id, category_id, location_id, title[:255], description[:2000],
                                        price, currency, status, is_active, random.randint(
                                            1, 720)
                                        )

            relevant_tags = []
            if category_name == "Авто":
                relevant_tags = ["торг", "гарантия", "в наличии"]
            elif category_name == "Недвижимость":
                relevant_tags = ["без посредников",
                                 "ипотека", "возможен обмен"]
            elif category_name == "Электроника":
                relevant_tags = ["оригинал", "в коробке", "гарантия"]
            else:
                relevant_tags = ["б/у", "торг", "в наличии"]

            selected_tags = random.sample(relevant_tags, min(
                len(relevant_tags), random.randint(1, 3)))
            for tag_name in selected_tags:
                tag_id = tag_ids.get(tag_name)
                if tag_id:
                    await conn.execute("""
                        INSERT INTO ad_tags (ad_id, tag_id)
                        VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                    """, ad_id, tag_id)

            if i % 10 == 0:
                urgent_tag_id = tag_ids.get("срочная продажа")
                if urgent_tag_id:
                    await conn.execute("""
                        INSERT INTO ad_tags (ad_id, tag_id)
                        VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                    """, ad_id, urgent_tag_id)

    print(f"Объявления ({count}) загружены")


async def generate_favorites_and_views(pool: Pool):
    async with pool.acquire() as conn:
        user_ids = [r['id'] for r in await conn.fetch("SELECT id FROM users WHERE role = 'user'")]
        ad_ids = [r['id'] for r in await conn.fetch("SELECT id FROM ads WHERE is_active = true")]

        for user_id in user_ids:
            favorite_count = random.randint(0, 5)
            favorite_ads = random.sample(
                ad_ids, min(favorite_count, len(ad_ids)))
            for ad_id in favorite_ads:
                await conn.execute("""
                    INSERT INTO favorites (user_id, ad_id)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                """, user_id, ad_id)

        for ad_id in ad_ids:
            view_count = random.randint(5, 200)
            for _ in range(view_count):
                user_id = random.choice(user_ids + [None])
                device = random.choice(['MOBILE', 'PC'])
                viewed_at = fake.date_time_between(
                    start_date='-30d', end_date='now')

                await conn.execute("""
                    INSERT INTO views (ad_id, user_id, viewed_at, device)
                    VALUES ($1, $2, $3, $4)
                """, ad_id, user_id, viewed_at, device)

    print("Избранное и просмотры загружены")


async def generate_messages(pool: Pool):
    async with pool.acquire() as conn:
        ad_ids = [r['id'] for r in await conn.fetch("SELECT id FROM ads WHERE is_active = true")]
        user_ids = [r['id'] for r in await conn.fetch("SELECT id FROM users")]

        message_templates = {
            "Электроника": [
                "Здравствуйте! Подскажите, есть ли гарантия на товар?",
                "Можно посмотреть товар сегодня вечером?",
                "Есть ли возможность обмена на другую модель?",
                "Какой срок гарантии у этого устройства?"
            ],
            "Авто": [
                "Добрый день. Когда можно посмотреть автомобиль?",
                "Подскажите, сколько собственников по ПТС?",
                "Есть ли возможность тест-драйва?",
                "Какой реальный пробег у авто?"
            ],
            "Недвижимость": [
                "Здравствуйте. Можно посмотреть квартиру завтра?",
                "Есть ли в доме парковка?",
                "Какой ремонт в квартире — косметический или капитальный?",
                "Возможно ли рассмотреть вариант с ипотекой?"
            ],
            "default": [
                "Здравствуйте. Еще актуально?",
                "Какой минимальный торг?",
                "Можно забрать сегодня?",
                "Есть фото с другой стороны?"
            ]
        }

        for ad_id, user_id in zip(random.sample(ad_ids, min(100, len(ad_ids))), user_ids[:100]):
            category_name = await conn.fetchval("""
                SELECT c.name FROM ads a
                JOIN categories c ON c.id = a.category_id
                WHERE a.id = $1
            """, ad_id)

            templates = message_templates.get(
                category_name, message_templates["default"])

            for _ in range(random.randint(1, 5)):
                sender_id = random.choice([user_id, random.choice(user_ids)])
                if sender_id == user_id:
                    other_users = [u for u in user_ids if u != user_id]
                    if not other_users:
                        continue
                    recipient_id = random.choice(other_users)
                else:
                    recipient_id = user_id

                text = random.choice(templates)
                if "смотреть" in text or "посмотреть" in text:
                    text += f" {fake.time(pattern='%H:%M')}"

                sent_at = fake.date_time_between(
                    start_date='-7d', end_date='now')

                await conn.execute("""
                    INSERT INTO messages (sender_id, recipient_id, ad_id, text, sent_at)
                    VALUES ($1, $2, $3, $4, $5)
                """, sender_id, recipient_id, ad_id, text[:500], sent_at)

    print("Сообщения загружены")


async def generate_reports(pool: Pool):
    async with pool.acquire() as conn:
        ad_ids = [r['id'] for r in await conn.fetch("SELECT id FROM ads WHERE is_active = true")]
        user_ids = [r['id'] for r in await conn.fetch("SELECT id FROM users WHERE role = 'user'")]

        report_templates = [
            ("FRAUD", "Подозреваю мошенничество. Продавец просит перевести деньги на карту Сбербанка, но не дает посмотреть товар"),
            ("INAPPROPRIATE_CONTENT", "На фото неприемлемый контент — обнаженное тело"),
            ("SPAM", "Объявление дублируется 5 раз в разных категориях"),
            ("COPYRIGHT", "Используются мои фотографии без разрешения"),
            ("FAKE_PROFILE", "Подозреваю, что продавец использует чужую личность"),
            ("OTHER", "Цена в объявлении не соответствует реальной. При переписке просят на 30% больше")
        ]

        for _ in range(20):
            ad_id = random.choice(ad_ids)
            complainant_id = random.choice(user_ids)

            reported_user_id = await conn.fetchval("SELECT user_id FROM ads WHERE id = $1", ad_id)
            if reported_user_id is None:
                continue

            reason, template = random.choice(report_templates)

            description = template
            if reason == "FRAUD":
                description += f". Номер карты, на которую просят перевести: **** **** **** {random.randint(1000, 9999)}"
            elif reason == "COPYRIGHT":
                description += f". Мои оригинальные фото можно найти здесь: https://example.com/original-{random.randint(100, 999)}"

            created_at = fake.date_time_between(
                start_date='-14d', end_date='-1d')
            status = random.choice(['PENDING', 'RESOLVED', 'REJECTED'])

            await conn.execute("""
                INSERT INTO reports (ad_id, complainant_id, reported_user_id, reason, description, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, ad_id, complainant_id, reported_user_id, reason, description[:300], status, created_at)

    print("Жалобы загружены")


async def main():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not set in .env")

    pool = await create_pool(DATABASE_URL)

    print("Начинаем генерацию реалистичных данных")
    try:
        print("=" * 50)
        # Последовательная генерация данных
        await generate_categories(pool)
        await generate_tags(pool)
        await generate_users(pool, 100)
        await generate_locations(pool, 50)
        await generate_ads(pool, 5000)
        await generate_favorites_and_views(pool)
        await generate_messages(pool)
        await generate_reports(pool)

        print("=" * 50)
        print(
            "Все данные успешно загружены!")

    finally:
        await pool.close()

if __name__ == "__main__":
    asyncio.run(main())
