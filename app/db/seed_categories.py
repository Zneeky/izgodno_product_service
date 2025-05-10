import uuid
from app.models.category import Category

async def seed_categories_from_txt(session, file_path: str):
    category_map = {}  # maps full path to Category object
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    for line in lines:
        parts = [p.strip() for p in line.split(">")]
        full_path = ""
        parent = None

        for part in parts:
            full_path = f"{full_path} > {part}" if full_path else part
            if full_path in category_map:
                parent = category_map[full_path]
                continue

            slug = part.lower().replace(" ", "-")
            category = Category(
                id=uuid.uuid4(),
                name=part,
                slug=slug,
                parent_id=parent.id if parent else None,
            )
            session.add(category)
            await session.flush()  # To get the category ID
            category_map[full_path] = category
            parent = category

    await session.commit()
    print("🌱 Categories seeded from file.")