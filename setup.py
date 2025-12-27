"""Script de configuration du projet."""

from setuptools import find_packages, setup

setup(
    name="extracteur-data",
    version="1.0.0",
    description="Système d'extraction et prétraitement de données multi-formats",
    author="",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "python-multipart>=0.0.6",
        "pdfplumber>=0.10.3",
        "PyMuPDF>=1.23.8",
        "openpyxl>=3.1.2",
        "python-docx>=1.1.0",
        "pytesseract>=0.3.10",
        "Pillow>=10.1.0",
        "spacy>=3.7.2",
        "sqlalchemy[asyncio]>=2.0.23",
        "alembic>=1.12.1",
        "asyncpg>=0.29.0",
        "aiosqlite>=0.19.0",
        "aiofiles>=23.2.1",
        "python-dotenv>=1.0.0",
        "pythonjsonlogger>=2.0.7",
    ],
)

