from fastapi import FastAPI
import pickle

app = FastAPI()

with open("model.pkl", "rb") as f:
    model = pickle.load(f)


@app.get("/")
def home():
    return {"message": "ML model server is running"}


@app.post("/predict")
def predict(data: dict):

    X = [[
        data["area"],
        data["rooms"]
    ]]

    prediction = model.predict(X)[0]

    return {
        "prediction": float(prediction)
    }
