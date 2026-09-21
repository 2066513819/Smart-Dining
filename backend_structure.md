# 餐饮推荐系统后端

## 项目结构
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── dish.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── dish.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── recommendation.py
│   │   └── dish.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── dify_service.py
│   │   └── db_service.py
│   └── config.py
├── requirements.txt
└── .env
```

## 技术栈
- FastAPI
- SQLAlchemy
- Pydantic
- JWT
- Requests