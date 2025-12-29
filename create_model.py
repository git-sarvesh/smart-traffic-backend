import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Synthetic traffic data (trained on Google Colab patterns)
hours = np.random.randint(0, 24, 1000)
days = np.random.randint(0, 7, 1000)
traffic = np.random.randint(0, 15, 1000)
congestion = np.where((hours > 7) & (hours < 10) | (hours > 17) & (hours < 20), 2,
             np.where((hours > 11) & (hours < 14), 1, 0))

X = np.column_stack([hours, days, traffic])
y = congestion
X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2)

model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)
joblib.dump(model, 'congestion_model.pkl')
print("✅ ML Model created! Ready for deployment.")
