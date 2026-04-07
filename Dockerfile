FROM freqtradeorg/freqtrade:stable

WORKDIR /app

# Extra scientific stack used by the adaptive system
RUN pip install --no-cache-dir pandas numpy ta scikit-learn optuna pytest

COPY . /app

ENV PYTHONPATH=/app

# Default command can be overridden by docker run
CMD ["freqtrade", "--help"]
