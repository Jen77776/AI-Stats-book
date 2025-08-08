# seed_database.py

import random
from faker import Faker
from app import app, db, Response # 从您的主应用中导入app, db和Response模型

# --- 配置 ---
NUMBER_OF_FAKE_ENTRIES = 20 # 您要求的20条假数据
FAKE_ANSWERS = [
    "I think the worst part is the y-axis, the intervals are not even and it's very misleading.",
    "The colors are too bright and the green arrow doesn't seem to mean anything. The y-axis is also confusing.",
    "Three bad practices are: 1. The non-linear y-axis. 2. Chart junk like the arrow. 3. No axis titles. The axis is the worst because it breaks the fundamental rules of data representation.",
    "I don't know, it looks fine to me.",
    "The data shows a clear upward trend, which is emphasized by the arrow. However, the axis labels are hard to read.",
    "Why is Q1P different? It's not explained. Also, the y-axis jumps from 50M to 200M, which feels wrong.",
]
FAKE_COMMENTS = [
    "The AI feedback was very helpful, it pointed out exactly what I missed.",
    "Good feedback.",
    "", # 模拟用户不留评论
    "I still don't understand why the axis is the worst part.",
    "This was a useful exercise.",
    "The AI was a bit too harsh in its critique.",
]

# --- 主函数 ---
def seed_data():
    # 创建一个Faker实例
    fake = Faker()
    
    # 使用app_context来确保数据库连接正确
    with app.app_context():
        print(f"Connecting to database...")
        
        print(f"Deleting old data from the 'responses' table...")
        # 为了避免重复，我们先清空旧数据
        db.session.query(Response).delete()
        db.session.commit()

        print(f"Creating {NUMBER_OF_FAKE_ENTRIES} new fake entries...")
        # 循环创建新的数据对象
        for i in range(NUMBER_OF_FAKE_ENTRIES):
            # 随机决定这条假数据是否被标记为AI生成
            is_ai = random.choice([True, False])
            
            new_response = Response(
                student_id=f"fake_{fake.user_name()}",
                question="dataviz_critique", # 使用prompt_id
                student_answer=random.choice(FAKE_ANSWERS),
                ai_feedback="This is a generated AI feedback for a fake entry.",
                timestamp=fake.date_time_this_year(),
                rating=random.randint(1, 5),
                feedback_comment=random.choice(FAKE_COMMENTS),
                is_ai_generated=is_ai
            )
            db.session.add(new_response) # 将新对象添加到“待办列表”

        # 一次性将所有新数据提交到数据库，效率更高
        db.session.commit()
        print(f"Successfully seeded the database with {NUMBER_OF_FAKE_ENTRIES} entries!")

if __name__ == '__main__':
    seed_data()