from setuptools import setup, find_packages

setup(
    name="sentiment_analysis",
    version="0.1.0",
    packages=find_packages(include=['sentiment_analysis', 'sentiment_analysis.*']),
    install_requires=[
        "pandas",
        "openai",
        "python-dotenv",
        "tqdm",
        "backoff"
    ],
    author="Legal Team Sentiment Analysis",
    description="Sentiment analysis tool for message data",
    python_requires=">=3.8"
)

