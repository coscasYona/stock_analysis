from setuptools import setup, find_packages

setup(
    name="stock_analysis",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "yfinance>=0.2.36",
        "optuna>=3.5.0",
        "matplotlib>=3.8.0",
        "SQLAlchemy>=2.0.0",
        "alembic>=1.13.0",
        "pytest>=7.4.0",
        "pytest-cov>=4.1.0",
        "python-dotenv>=1.0.0",
        "plotly>=5.18.0",
        "scikit-learn>=1.3.0",
        "ta>=0.10.0"
    ],
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="A stock analysis and trading strategy framework",
    keywords="stock, trading, analysis, finance",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 