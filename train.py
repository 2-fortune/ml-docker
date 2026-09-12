from sklearn.linear_model import LinearRegression
import pickle

X = [
    [50, 1],
    [60, 2],
    [70, 2],
    [80, 3],
    [90, 3],
    [100, 4],
]

y = [
    3.0,
    3.8,
    4.2,
    5.0,
    5.8,
    6.5,
]

# 모델 생성
model = LinearRegression()

# 학습
model.fit(X, y)

# 모델 저장
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model training completed.")
