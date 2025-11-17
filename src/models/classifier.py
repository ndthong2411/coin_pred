"""
ML classifier for price prediction using XGBoost.
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from pathlib import Path
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import xgboost as xgb
from config import settings
from src.utils import log


class PriceClassifier:
    """
    Classify price movements using XGBoost.
    Predicts: UP, DOWN, or NEUTRAL
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize classifier.

        Args:
            model_path: Path to saved model
        """
        self.model = None
        self.feature_columns = None
        self.scaler = None

        if model_path and Path(model_path).exists():
            self.load_model(model_path)

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features from DataFrame with indicators.

        Args:
            df: DataFrame with indicators

        Returns:
            Feature DataFrame
        """
        # Select feature columns (exclude target and metadata)
        exclude_cols = ['timestamp', 'symbol', 'id', 'created_at']
        feature_cols = [col for col in df.columns if col not in exclude_cols]

        # Fill NaN
        features = df[feature_cols].fillna(method='ffill').fillna(0)

        # Store feature columns
        if self.feature_columns is None:
            self.feature_columns = feature_cols

        return features

    def create_target(self, df: pd.DataFrame, horizon: int = 15) -> pd.Series:
        """
        Create target variable (UP/DOWN/NEUTRAL).

        Args:
            df: DataFrame with 'close' price
            horizon: Minutes ahead to predict

        Returns:
            Target series
        """
        # Calculate future return
        future_return = df['close'].shift(-horizon) / df['close'] - 1

        # Classify
        # UP if return > 0.3%, DOWN if return < -0.3%, else NEUTRAL
        target = pd.Series('NEUTRAL', index=df.index)
        target[future_return > 0.003] = 'UP'
        target[future_return < -0.003] = 'DOWN'

        return target

    def train(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2,
        horizon: int = 15
    ) -> Dict:
        """
        Train the model.

        Args:
            df: DataFrame with features
            test_size: Test set proportion
            horizon: Prediction horizon in minutes

        Returns:
            Training metrics
        """
        log.info("Training XGBoost classifier...")

        # Prepare features and target
        X = self.prepare_features(df)
        y = self.create_target(df, horizon)

        # Remove rows with NaN target (at the end)
        valid_idx = y.notna()
        X = X[valid_idx]
        y = y[valid_idx]

        # Encode target
        label_map = {'UP': 2, 'NEUTRAL': 1, 'DOWN': 0}
        y_encoded = y.map(label_map)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=test_size, shuffle=False  # Time-series, no shuffle
        )

        log.info(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
        log.info(f"Class distribution: {y.value_counts().to_dict()}")

        # Train XGBoost
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            objective='multi:softmax',
            num_class=3,
            random_state=42,
            n_jobs=-1
        )

        self.model.fit(
            X_train,
            y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )

        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        log.info(f"Model accuracy: {accuracy:.2%}")

        # Classification report
        target_names = ['DOWN', 'NEUTRAL', 'UP']
        report = classification_report(y_test, y_pred, target_names=target_names, output_dict=True)

        log.info("\nClassification Report:")
        log.info(classification_report(y_test, y_pred, target_names=target_names))

        return {
            'accuracy': accuracy,
            'classification_report': report,
            'feature_importance': dict(zip(X.columns, self.model.feature_importances_))
        }

    def predict(self, df: pd.DataFrame) -> Dict:
        """
        Predict on new data.

        Args:
            df: DataFrame with features (latest candle)

        Returns:
            Prediction dict
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")

        # Prepare features
        X = self.prepare_features(df)

        # Ensure same columns as training
        if self.feature_columns:
            missing_cols = set(self.feature_columns) - set(X.columns)
            for col in missing_cols:
                X[col] = 0
            X = X[self.feature_columns]

        # Predict
        pred_encoded = self.model.predict(X)
        pred_proba = self.model.predict_proba(X)

        # Decode
        label_decode = {0: 'DOWN', 1: 'NEUTRAL', 2: 'UP'}
        prediction = label_decode[pred_encoded[-1]]
        confidence = float(pred_proba[-1].max())

        return {
            'prediction': prediction,
            'confidence': confidence,
            'probabilities': {
                'DOWN': float(pred_proba[-1][0]),
                'NEUTRAL': float(pred_proba[-1][1]),
                'UP': float(pred_proba[-1][2])
            },
            'model': 'XGBoost'
        }

    def save_model(self, path: str):
        """Save model to disk."""
        model_data = {
            'model': self.model,
            'feature_columns': self.feature_columns,
        }
        joblib.dump(model_data, path)
        log.info(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load model from disk."""
        model_data = joblib.load(path)
        self.model = model_data['model']
        self.feature_columns = model_data['feature_columns']
        log.info(f"Model loaded from {path}")


if __name__ == "__main__":
    # Test classifier
    from src.data_collection import binance_client
    from src.feature_engineering import calculate_indicators_for_symbol

    print("Testing Price Classifier...")

    # Get data
    df = binance_client.get_historical_klines("BTC/USDT", "1h", limit=1000)
    df = calculate_indicators_for_symbol(df)

    print(f"Data shape: {df.shape}")

    # Train model
    classifier = PriceClassifier()
    metrics = classifier.train(df, test_size=0.2, horizon=6)  # 6 hours ahead

    print(f"\nAccuracy: {metrics['accuracy']:.2%}")

    # Test prediction
    pred = classifier.predict(df.tail(1))
    print(f"\nPrediction: {pred['prediction']}")
    print(f"Confidence: {pred['confidence']:.2%}")
    print(f"Probabilities: {pred['probabilities']}")

    # Save model
    model_path = settings.project_root / "data" / "models" / "xgboost_btc.pkl"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    classifier.save_model(str(model_path))

    print(f"\n✅ Model saved to {model_path}")
