import os

import json

import joblib

from .config import MODEL_DIR, PARAM_FILE, TARGETS

def load_best_params():

    with open(PARAM_FILE, "r") as f:

        return json.load(f)
    
def save_model(model, symbol, target):

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = MODEL_DIR / f"{symbol}_{target}.joblib"

    joblib.dump(model, filename)

def load_model(symbol, target):

    filename = MODEL_DIR / f"{symbol}_{target}.joblib"

    if not os.path.exists(filename):
        raise FileNotFoundError(
            f"Model {filename} tidak ditemukan."
        )

    return joblib.load(filename)

def load_all_models(symbols):

    models = {}

    for symbol in symbols:

        models[symbol] = {}

        for target in TARGETS:

            models[symbol][target] = load_model(
                symbol,
                target
            )

    return models

def load_best_params():

    with open(PARAM_FILE, "r") as f:

        return json.load(f)