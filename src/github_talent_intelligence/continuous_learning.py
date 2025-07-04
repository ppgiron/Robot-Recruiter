import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pickle
import hashlib
from pathlib import Path
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
import threading
import time
import queue

logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    CLIENT_SATISFACTION = "client_satisfaction"
    PLACEMENT_SUCCESS = "placement_success"
    CANDIDATE_MATCH_QUALITY = "candidate_match_quality"
    REQUIREMENT_EXTRACTION_ACCURACY = "requirement_extraction_accuracy"
    QUESTION_GENERATION_QUALITY = "question_generation_quality"
    RECRUITER_ACTION = "recruiter_action"

class FeedbackSource(Enum):
    CLIENT_RESPONSE = "client_response"
    PLACEMENT_OUTCOME = "placement_outcome"
    RECRUITER_ACTION = "recruiter_action"
    AUTOMATED_ANALYSIS = "automated_analysis"
    USER_FEEDBACK = "user_feedback"

@dataclass
class FeedbackData:
    id: str
    feedback_type: FeedbackType
    source: FeedbackSource
    session_id: Optional[str]
    candidate_id: Optional[str]
    client_id: Optional[str]
    placement_id: Optional[str]
    score: float  # 0-1 scale
    metadata: Dict[str, Any]
    timestamp: datetime
    processed: bool = False

@dataclass
class ModelPerformance:
    model_name: str
    version: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_samples: int
    test_samples: int
    last_updated: datetime
    performance_trend: List[float]

@dataclass
class LearningSignal:
    feature_name: str
    importance_score: float
    direction: str  # "increase", "decrease", "maintain"
    confidence: float
    sample_size: int
    timestamp: datetime

class ContinuousLearningSystem:
    def __init__(self, db_url: str = "sqlite:///robot_recruiter.db"):
        self.db_url = db_url
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Model storage
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        # Feedback processing
        self.feedback_queue = queue.Queue()
        self.processing_thread = None
        self.is_running = False
        
        # Model registry
        self.active_models: Dict[str, Any] = {}
        self.model_versions: Dict[str, List[str]] = {}
        self.performance_history: Dict[str, List[ModelPerformance]] = {}
        
        # Learning parameters
        self.learning_rate = 0.01
        self.min_samples_for_update = 50
        self.performance_threshold = 0.7
        self.retrain_interval_hours = 24
        
        # Initialize models
        self._initialize_models()
        self._start_feedback_processor()
    
    def _initialize_models(self):
        """Initialize or load existing models."""
        models_to_initialize = [
            "candidate_matching",
            "requirement_extraction", 
            "question_generation",
            "placement_success_prediction"
        ]
        
        for model_name in models_to_initialize:
            model_path = self.models_dir / f"{model_name}_latest.pkl"
            
            if model_path.exists():
                # Load existing model
                self.active_models[model_name] = joblib.load(model_path)
                logger.info(f"Loaded existing model: {model_name}")
            else:
                # Initialize new model
                self.active_models[model_name] = self._create_new_model(model_name)
                self._save_model(model_name, self.active_models[model_name])
                logger.info(f"Initialized new model: {model_name}")
    
    def _create_new_model(self, model_name: str) -> Any:
        """Create a new model based on the model type."""
        if model_name == "candidate_matching":
            return RandomForestRegressor(n_estimators=100, random_state=42)
        elif model_name == "requirement_extraction":
            return LogisticRegression(random_state=42)
        elif model_name == "question_generation":
            return RandomForestRegressor(n_estimators=50, random_state=42)
        elif model_name == "placement_success_prediction":
            return LogisticRegression(random_state=42)
        else:
            raise ValueError(f"Unknown model type: {model_name}")
    
    def _start_feedback_processor(self):
        """Start the background feedback processing thread."""
        self.is_running = True
        self.processing_thread = threading.Thread(target=self._feedback_processing_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        logger.info("Started feedback processing thread")
    
    def _feedback_processing_loop(self):
        """Background loop for processing feedback."""
        while self.is_running:
            try:
                # Process feedback in batches
                feedback_batch = []
                while len(feedback_batch) < 10:  # Process in batches of 10
                    try:
                        feedback = self.feedback_queue.get(timeout=1)
                        feedback_batch.append(feedback)
                    except queue.Empty:
                        break
                
                if feedback_batch:
                    self._process_feedback_batch(feedback_batch)
                
                # Check if models need retraining
                self._check_model_retraining()
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in feedback processing loop: {e}")
                time.sleep(10)  # Wait longer on error
    
    def _process_feedback_batch(self, feedback_batch: List[FeedbackData]):
        """Process a batch of feedback data."""
        logger.info(f"Processing {len(feedback_batch)} feedback items")
        
        # Group feedback by type
        feedback_by_type = {}
        for feedback in feedback_batch:
            if feedback.feedback_type not in feedback_by_type:
                feedback_by_type[feedback.feedback_type] = []
            feedback_by_type[feedback.feedback_type].append(feedback)
        
        # Process each feedback type
        for feedback_type, feedbacks in feedback_by_type.items():
            self._process_feedback_type(feedback_type, feedbacks)
        
        # Mark feedback as processed
        self._mark_feedback_processed([f.id for f in feedback_batch])
    
    def _process_feedback_type(self, feedback_type: FeedbackType, feedbacks: List[FeedbackData]):
        """Process feedback of a specific type."""
        if feedback_type == FeedbackType.CANDIDATE_MATCH_QUALITY:
            self._update_candidate_matching_model(feedbacks)
        elif feedback_type == FeedbackType.REQUIREMENT_EXTRACTION_ACCURACY:
            self._update_requirement_extraction_model(feedbacks)
        elif feedback_type == FeedbackType.QUESTION_GENERATION_QUALITY:
            self._update_question_generation_model(feedbacks)
        elif feedback_type == FeedbackType.PLACEMENT_SUCCESS:
            self._update_placement_success_model(feedbacks)
    
    def _update_candidate_matching_model(self, feedbacks: List[FeedbackData]):
        """Update candidate matching model with new feedback."""
        try:
            # Extract features and labels from feedback
            features = []
            labels = []
            
            for feedback in feedbacks:
                # Extract features from metadata
                feature_vector = self._extract_candidate_matching_features(feedback)
                if feature_vector is not None:
                    features.append(feature_vector)
                    labels.append(feedback.score)
            
            if len(features) >= self.min_samples_for_update:
                # Convert to numpy arrays
                X = np.array(features)
                y = np.array(labels)
                
                # Update model (online learning)
                model = self.active_models["candidate_matching"]
                model.fit(X, y)
                
                # Save updated model
                self._save_model("candidate_matching", model)
                
                logger.info(f"Updated candidate matching model with {len(features)} samples")
                
        except Exception as e:
            logger.error(f"Error updating candidate matching model: {e}")
    
    def _extract_candidate_matching_features(self, feedback: FeedbackData) -> Optional[List[float]]:
        """Extract features for candidate matching from feedback."""
        try:
            metadata = feedback.metadata
            
            # Extract relevant features
            features = [
                metadata.get("skill_match_score", 0.0),
                metadata.get("experience_match_score", 0.0),
                metadata.get("culture_match_score", 0.0),
                metadata.get("location_match_score", 0.0),
                metadata.get("salary_match_score", 0.0),
                metadata.get("availability_match_score", 0.0),
                metadata.get("communication_score", 0.0),
                metadata.get("technical_assessment_score", 0.0),
                metadata.get("client_preference_score", 0.0),
                metadata.get("market_demand_score", 0.0)
            ]
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting candidate matching features: {e}")
            return None
    
    def _update_requirement_extraction_model(self, feedbacks: List[FeedbackData]):
        """Update requirement extraction model with new feedback."""
        try:
            features = []
            labels = []
            
            for feedback in feedbacks:
                feature_vector = self._extract_requirement_features(feedback)
                if feature_vector is not None:
                    features.append(feature_vector)
                    labels.append(1 if feedback.score > 0.5 else 0)  # Binary classification
            
            if len(features) >= self.min_samples_for_update:
                X = np.array(features)
                y = np.array(labels)
                
                model = self.active_models["requirement_extraction"]
                model.fit(X, y)
                
                self._save_model("requirement_extraction", model)
                logger.info(f"Updated requirement extraction model with {len(features)} samples")
                
        except Exception as e:
            logger.error(f"Error updating requirement extraction model: {e}")
    
    def _extract_requirement_features(self, feedback: FeedbackData) -> Optional[List[float]]:
        """Extract features for requirement extraction from feedback."""
        try:
            metadata = feedback.metadata
            
            features = [
                metadata.get("text_length", 0.0),
                metadata.get("technical_terms_count", 0.0),
                metadata.get("experience_indicators", 0.0),
                metadata.get("skill_mentions", 0.0),
                metadata.get("timeline_indicators", 0.0),
                metadata.get("location_indicators", 0.0),
                metadata.get("salary_indicators", 0.0),
                metadata.get("team_size_indicators", 0.0),
                metadata.get("culture_indicators", 0.0),
                metadata.get("confidence_score", 0.0)
            ]
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting requirement features: {e}")
            return None
    
    def _update_question_generation_model(self, feedbacks: List[FeedbackData]):
        """Update question generation model with new feedback."""
        try:
            features = []
            labels = []
            
            for feedback in feedbacks:
                feature_vector = self._extract_question_features(feedback)
                if feature_vector is not None:
                    features.append(feature_vector)
                    labels.append(feedback.score)
            
            if len(features) >= self.min_samples_for_update:
                X = np.array(features)
                y = np.array(labels)
                
                model = self.active_models["question_generation"]
                model.fit(X, y)
                
                self._save_model("question_generation", model)
                logger.info(f"Updated question generation model with {len(features)} samples")
                
        except Exception as e:
            logger.error(f"Error updating question generation model: {e}")
    
    def _extract_question_features(self, feedback: FeedbackData) -> Optional[List[float]]:
        """Extract features for question generation from feedback."""
        try:
            metadata = feedback.metadata
            
            features = [
                metadata.get("question_relevance", 0.0),
                metadata.get("information_gap_score", 0.0),
                metadata.get("priority_score", 0.0),
                metadata.get("context_relevance", 0.0),
                metadata.get("clarity_score", 0.0),
                metadata.get("actionability_score", 0.0),
                metadata.get("timing_relevance", 0.0),
                metadata.get("client_engagement", 0.0),
                metadata.get("follow_up_potential", 0.0),
                metadata.get("conversation_flow", 0.0)
            ]
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting question features: {e}")
            return None
    
    def _update_placement_success_model(self, feedbacks: List[FeedbackData]):
        """Update placement success prediction model with new feedback."""
        try:
            features = []
            labels = []
            
            for feedback in feedbacks:
                feature_vector = self._extract_placement_features(feedback)
                if feature_vector is not None:
                    features.append(feature_vector)
                    labels.append(1 if feedback.score > 0.5 else 0)  # Binary classification
            
            if len(features) >= self.min_samples_for_update:
                X = np.array(features)
                y = np.array(labels)
                
                model = self.active_models["placement_success_prediction"]
                model.fit(X, y)
                
                self._save_model("placement_success_prediction", model)
                logger.info(f"Updated placement success model with {len(features)} samples")
                
        except Exception as e:
            logger.error(f"Error updating placement success model: {e}")
    
    def _extract_placement_features(self, feedback: FeedbackData) -> Optional[List[float]]:
        """Extract features for placement success prediction from feedback."""
        try:
            metadata = feedback.metadata
            
            features = [
                metadata.get("candidate_quality_score", 0.0),
                metadata.get("client_satisfaction", 0.0),
                metadata.get("skill_match_percentage", 0.0),
                metadata.get("experience_match", 0.0),
                metadata.get("culture_fit_score", 0.0),
                metadata.get("salary_negotiation_success", 0.0),
                metadata.get("timeline_compliance", 0.0),
                metadata.get("communication_quality", 0.0),
                metadata.get("technical_assessment", 0.0),
                metadata.get("market_conditions", 0.0)
            ]
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting placement features: {e}")
            return None
    
    def _save_model(self, model_name: str, model: Any):
        """Save a model with versioning."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version = f"v{timestamp}"
        
        # Save new version
        model_path = self.models_dir / f"{model_name}_{version}.pkl"
        joblib.dump(model, model_path)
        
        # Update latest
        latest_path = self.models_dir / f"{model_name}_latest.pkl"
        joblib.dump(model, latest_path)
        
        # Track version
        if model_name not in self.model_versions:
            self.model_versions[model_name] = []
        self.model_versions[model_name].append(version)
        
        # Keep only last 5 versions
        if len(self.model_versions[model_name]) > 5:
            old_version = self.model_versions[model_name].pop(0)
            old_path = self.models_dir / f"{model_name}_{old_version}.pkl"
            if old_path.exists():
                old_path.unlink()
        
        logger.info(f"Saved model {model_name} version {version}")
    
    def _mark_feedback_processed(self, feedback_ids: List[str]):
        """Mark feedback as processed in the database."""
        try:
            session = self.Session()
            for feedback_id in feedback_ids:
                session.execute(
                    text("UPDATE feedback_data SET processed = 1 WHERE id = :feedback_id"),
                    {"feedback_id": feedback_id}
                )
            session.commit()
            session.close()
        except Exception as e:
            logger.error(f"Error marking feedback as processed: {e}")
    
    def _check_model_retraining(self):
        """Check if models need full retraining."""
        try:
            # Check performance metrics
            for model_name in self.active_models.keys():
                performance = self._evaluate_model_performance(model_name)
                
                if performance and performance.accuracy < self.performance_threshold:
                    logger.warning(f"Model {model_name} performance below threshold: {performance.accuracy}")
                    self._trigger_full_retraining(model_name)
                    
        except Exception as e:
            logger.error(f"Error checking model retraining: {e}")
    
    def _evaluate_model_performance(self, model_name: str) -> Optional[ModelPerformance]:
        """Evaluate model performance on recent data."""
        try:
            # Get recent test data
            test_data = self._get_recent_test_data(model_name)
            if not test_data or len(test_data) < 10:
                return None
            
            # Evaluate model
            model = self.active_models[model_name]
            X_test, y_test = test_data
            
            if hasattr(model, 'predict_proba'):
                y_pred_proba = model.predict_proba(X_test)
                y_pred = (y_pred_proba[:, 1] > 0.5).astype(int)
            else:
                y_pred = model.predict(X_test)
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, y_pred)
            precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary')
            
            performance = ModelPerformance(
                model_name=model_name,
                version=self.model_versions[model_name][-1] if model_name in self.model_versions else "unknown",
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                training_samples=len(X_test),
                test_samples=len(y_test),
                last_updated=datetime.now(timezone.utc),
                performance_trend=[]
            )
            
            # Store performance history
            if model_name not in self.performance_history:
                self.performance_history[model_name] = []
            self.performance_history[model_name].append(performance)
            
            return performance
            
        except Exception as e:
            logger.error(f"Error evaluating model performance: {e}")
            return None
    
    def _get_recent_test_data(self, model_name: str) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Get recent test data for model evaluation."""
        try:
            # This would typically query your database for recent feedback
            # For now, return None to indicate no test data available
            return None
        except Exception as e:
            logger.error(f"Error getting test data: {e}")
            return None
    
    def _trigger_full_retraining(self, model_name: str):
        """Trigger full model retraining."""
        logger.info(f"Triggering full retraining for model: {model_name}")
        # This would typically trigger a full retraining pipeline
        # For now, just log the event
    
    def add_feedback(self, feedback: FeedbackData):
        """Add feedback to the processing queue."""
        self.feedback_queue.put(feedback)
        logger.info(f"Added feedback to queue: {feedback.feedback_type.value}")
    
    def get_model_performance(self, model_name: str) -> Optional[ModelPerformance]:
        """Get current model performance."""
        return self._evaluate_model_performance(model_name)
    
    def get_learning_signals(self) -> List[LearningSignal]:
        """Get learning signals from recent feedback."""
        try:
            signals = []
            
            # Analyze feature importance changes
            for model_name, model in self.active_models.items():
                if hasattr(model, 'feature_importances_'):
                    importances = model.feature_importances_
                    feature_names = self._get_feature_names(model_name)
                    
                    for i, importance in enumerate(importances):
                        if i < len(feature_names):
                            signal = LearningSignal(
                                feature_name=feature_names[i],
                                importance_score=float(importance),
                                direction="maintain",  # Would be calculated based on trends
                                confidence=0.8,  # Would be calculated based on variance
                                sample_size=100,  # Would be actual sample size
                                timestamp=datetime.now(timezone.utc)
                            )
                            signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error getting learning signals: {e}")
            return []
    
    def _get_feature_names(self, model_name: str) -> List[str]:
        """Get feature names for a model."""
        feature_maps = {
            "candidate_matching": [
                "skill_match_score", "experience_match_score", "culture_match_score",
                "location_match_score", "salary_match_score", "availability_match_score",
                "communication_score", "technical_assessment_score", "client_preference_score",
                "market_demand_score"
            ],
            "requirement_extraction": [
                "text_length", "technical_terms_count", "experience_indicators",
                "skill_mentions", "timeline_indicators", "location_indicators",
                "salary_indicators", "team_size_indicators", "culture_indicators",
                "confidence_score"
            ],
            "question_generation": [
                "question_relevance", "information_gap_score", "priority_score",
                "context_relevance", "clarity_score", "actionability_score",
                "timing_relevance", "client_engagement", "follow_up_potential",
                "conversation_flow"
            ],
            "placement_success_prediction": [
                "candidate_quality_score", "client_satisfaction", "skill_match_percentage",
                "experience_match", "culture_fit_score", "salary_negotiation_success",
                "timeline_compliance", "communication_quality", "technical_assessment",
                "market_conditions"
            ]
        }
        
        return feature_maps.get(model_name, [])
    
    def shutdown(self):
        """Shutdown the continuous learning system."""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        logger.info("Continuous learning system shutdown complete")

# Global instance
continuous_learning = ContinuousLearningSystem() 