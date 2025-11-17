"""
Unit tests for PriceClassifier.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile

from src.models.classifier import PriceClassifier


@pytest.mark.unit
class TestPriceClassifier:
    """Test PriceClassifier class."""

    def test_initialization(self):
        """Test classifier initialization."""
        classifier = PriceClassifier()

        assert classifier.model is None
        assert classifier.feature_columns is None

    def test_prepare_features(self, sample_features):
        """Test feature preparation."""
        classifier = PriceClassifier()

        features = classifier.prepare_features(sample_features)

        assert isinstance(features, pd.DataFrame)
        assert len(features) == len(sample_features)
        assert not features.isnull().any().any()  # No NaN values

    def test_prepare_features_excludes_metadata(self):
        """Test that metadata columns are excluded."""
        classifier = PriceClassifier()

        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10),
            'symbol': ['BTC/USDT'] * 10,
            'close': np.random.rand(10) * 45000,
            'rsi_14': np.random.rand(10) * 100
        })

        features = classifier.prepare_features(df)

        assert 'timestamp' not in features.columns
        assert 'symbol' not in features.columns
        assert 'close' in features.columns
        assert 'rsi_14' in features.columns

    def test_create_target_up(self):
        """Test target creation for upward movement."""
        classifier = PriceClassifier()

        # Create prices that go up
        df = pd.DataFrame({
            'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        })

        target = classifier.create_target(df, horizon=1)

        # Most should be UP since prices increase
        assert 'UP' in target.values

    def test_create_target_down(self):
        """Test target creation for downward movement."""
        classifier = PriceClassifier()

        # Create prices that go down
        df = pd.DataFrame({
            'close': [100, 99, 98, 97, 96, 95, 94, 93, 92, 91]
        })

        target = classifier.create_target(df, horizon=1)

        # Most should be DOWN since prices decrease
        assert 'DOWN' in target.values

    def test_create_target_neutral(self):
        """Test target creation for sideways movement."""
        classifier = PriceClassifier()

        # Create prices with small changes
        df = pd.DataFrame({
            'close': [100 + np.random.randn()*0.1 for _ in range(100)]
        })

        target = classifier.create_target(df, horizon=1)

        # Should have some NEUTRAL values
        assert 'NEUTRAL' in target.values

    def test_train(self, sample_features):
        """Test model training."""
        classifier = PriceClassifier()

        # Add close price for target creation
        sample_features['close'] = 45000 + np.random.randn(len(sample_features)) * 500

        metrics = classifier.train(sample_features, test_size=0.2, horizon=5)

        assert classifier.model is not None
        assert 'accuracy' in metrics
        assert 0 <= metrics['accuracy'] <= 1
        assert 'classification_report' in metrics
        assert 'feature_importance' in metrics

    def test_predict_untrained_model(self, sample_features):
        """Test prediction with untrained model."""
        classifier = PriceClassifier()

        with pytest.raises(ValueError, match="Model not trained or loaded"):
            classifier.predict(sample_features)

    def test_predict_trained_model(self, sample_features):
        """Test prediction with trained model."""
        classifier = PriceClassifier()

        # Train model
        sample_features['close'] = 45000 + np.random.randn(len(sample_features)) * 500
        classifier.train(sample_features, test_size=0.2, horizon=5)

        # Predict on new data
        new_data = sample_features.tail(1)
        prediction = classifier.predict(new_data)

        assert 'prediction' in prediction
        assert prediction['prediction'] in ['UP', 'DOWN', 'NEUTRAL']
        assert 'confidence' in prediction
        assert 0 <= prediction['confidence'] <= 1
        assert 'probabilities' in prediction
        assert 'UP' in prediction['probabilities']
        assert 'DOWN' in prediction['probabilities']
        assert 'NEUTRAL' in prediction['probabilities']

    def test_save_and_load_model(self, sample_features):
        """Test model saving and loading."""
        classifier = PriceClassifier()

        # Train model
        sample_features['close'] = 45000 + np.random.randn(len(sample_features)) * 500
        classifier.train(sample_features, test_size=0.2, horizon=5)

        # Save model
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "test_model.pkl"
            classifier.save_model(str(model_path))

            assert model_path.exists()

            # Load model in new classifier
            new_classifier = PriceClassifier(model_path=str(model_path))

            assert new_classifier.model is not None
            assert new_classifier.feature_columns is not None

            # Test prediction
            prediction = new_classifier.predict(sample_features.tail(1))
            assert 'prediction' in prediction

    def test_predict_with_missing_columns(self, sample_features):
        """Test prediction when new data is missing some columns."""
        classifier = PriceClassifier()

        # Train with all features
        sample_features['close'] = 45000
        classifier.train(sample_features, test_size=0.2, horizon=5)

        # Create new data with missing column
        new_data = sample_features[['rsi_14', 'macd']].tail(1)

        # Should still work by filling missing columns with 0
        prediction = classifier.predict(new_data)

        assert 'prediction' in prediction

    def test_probability_sum_to_one(self, sample_features):
        """Test that probabilities sum to approximately 1."""
        classifier = PriceClassifier()

        sample_features['close'] = 45000 + np.random.randn(len(sample_features)) * 500
        classifier.train(sample_features, test_size=0.2, horizon=5)

        prediction = classifier.predict(sample_features.tail(1))

        prob_sum = sum(prediction['probabilities'].values())
        assert abs(prob_sum - 1.0) < 0.01  # Allow small floating point error
