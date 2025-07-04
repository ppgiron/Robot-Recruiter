#!/usr/bin/env python3
"""
Test script for the Continuous Learning System
Demonstrates feedback processing, model updates, and performance tracking.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import requests
import numpy as np

# API base URL
BASE_URL = "http://localhost:8000"

def generate_feedback_data(feedback_type: str, score: float, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate sample feedback data."""
    return {
        "feedback_type": feedback_type,
        "source": "automated_analysis",
        "session_id": str(uuid.uuid4()),
        "candidate_id": str(uuid.uuid4()),
        "client_id": str(uuid.uuid4()),
        "placement_id": str(uuid.uuid4()),
        "score": score,
        "metadata": metadata or {}
    }

def test_feedback_submission():
    """Test feedback submission for different types."""
    print("🔄 Testing Feedback Submission...")
    
    # Test candidate matching feedback
    candidate_feedback = generate_feedback_data(
        "candidate_match_quality",
        0.85,
        {
            "skill_match_score": 0.9,
            "experience_match_score": 0.8,
            "culture_match_score": 0.7,
            "location_match_score": 0.9,
            "salary_match_score": 0.8,
            "availability_match_score": 0.9,
            "communication_score": 0.8,
            "technical_assessment_score": 0.85,
            "client_preference_score": 0.8,
            "market_demand_score": 0.7
        }
    )
    
    response = requests.post(f"{BASE_URL}/learning/feedback", json=candidate_feedback)
    print(f"✅ Candidate matching feedback: {response.status_code}")
    
    # Test requirement extraction feedback
    requirement_feedback = generate_feedback_data(
        "requirement_extraction_accuracy",
        0.92,
        {
            "text_length": 1500,
            "technical_terms_count": 25,
            "experience_indicators": 8,
            "skill_mentions": 12,
            "timeline_indicators": 3,
            "location_indicators": 2,
            "salary_indicators": 1,
            "team_size_indicators": 1,
            "culture_indicators": 4,
            "confidence_score": 0.92
        }
    )
    
    response = requests.post(f"{BASE_URL}/learning/feedback", json=requirement_feedback)
    print(f"✅ Requirement extraction feedback: {response.status_code}")
    
    # Test question generation feedback
    question_feedback = generate_feedback_data(
        "question_generation_quality",
        0.78,
        {
            "question_relevance": 0.8,
            "information_gap_score": 0.7,
            "priority_score": 0.8,
            "context_relevance": 0.9,
            "clarity_score": 0.8,
            "actionability_score": 0.7,
            "timing_relevance": 0.8,
            "client_engagement": 0.8,
            "follow_up_potential": 0.7,
            "conversation_flow": 0.8
        }
    )
    
    response = requests.post(f"{BASE_URL}/learning/feedback", json=question_feedback)
    print(f"✅ Question generation feedback: {response.status_code}")

def test_placement_outcomes():
    """Test placement outcome recording."""
    print("\n🎯 Testing Placement Outcomes...")
    
    # Successful placement
    successful_placement = {
        "placement_id": str(uuid.uuid4()),
        "candidate_id": str(uuid.uuid4()),
        "client_id": str(uuid.uuid4()),
        "success": True,
        "satisfaction_score": 9.2,
        "duration_days": 45,
        "salary_achieved": 120000,
        "feedback_notes": "Excellent cultural fit and technical skills"
    }
    
    response = requests.post(f"{BASE_URL}/learning/placement-outcome", json=successful_placement)
    print(f"✅ Successful placement: {response.status_code}")
    
    # Failed placement
    failed_placement = {
        "placement_id": str(uuid.uuid4()),
        "candidate_id": str(uuid.uuid4()),
        "client_id": str(uuid.uuid4()),
        "success": False,
        "satisfaction_score": 3.5,
        "duration_days": 15,
        "salary_achieved": None,
        "feedback_notes": "Cultural mismatch and communication issues"
    }
    
    response = requests.post(f"{BASE_URL}/learning/placement-outcome", json=failed_placement)
    print(f"✅ Failed placement: {response.status_code}")

def test_model_performance():
    """Test model performance retrieval."""
    print("\n📊 Testing Model Performance...")
    
    models = ["candidate_matching", "requirement_extraction", "question_generation", "placement_success_prediction"]
    
    for model_name in models:
        try:
            response = requests.get(f"{BASE_URL}/learning/performance/{model_name}")
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    print(f"ℹ️  {model_name}: {data['message']}")
                else:
                    print(f"✅ {model_name}: Accuracy {data['accuracy']:.3f}, F1 {data['f1_score']:.3f}")
            else:
                print(f"❌ {model_name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {model_name}: Error - {e}")

def test_learning_signals():
    """Test learning signals retrieval."""
    print("\n🧠 Testing Learning Signals...")
    
    try:
        response = requests.get(f"{BASE_URL}/learning/signals")
        if response.status_code == 200:
            data = response.json()
            signals = data.get("signals", [])
            print(f"✅ Found {len(signals)} learning signals")
            
            for signal in signals[:5]:  # Show first 5 signals
                print(f"   • {signal['feature_name']}: {signal['importance_score']:.3f} ({signal['direction']})")
        else:
            print(f"❌ Learning signals: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Learning signals: Error - {e}")

def test_learning_analytics():
    """Test learning analytics retrieval."""
    print("\n📈 Testing Learning Analytics...")
    
    try:
        response = requests.get(f"{BASE_URL}/learning/analytics?days=30")
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Analytics for {data['period_days']} days:")
            
            # Feedback statistics
            feedback_stats = data.get("feedback_statistics", [])
            print(f"   📝 Feedback types: {len(feedback_stats)}")
            for stat in feedback_stats:
                print(f"      • {stat['type']}: {stat['count']} items, avg {stat['average_score']:.3f}")
            
            # Model performance
            model_perf = data.get("model_performance", [])
            print(f"   🤖 Models tracked: {len(model_perf)}")
            for model in model_perf:
                print(f"      • {model['model_name']}: {model['average_accuracy']:.3f} accuracy")
            
            # Placement analytics
            placement = data.get("placement_analytics", {})
            print(f"   🎯 Placement success rate: {placement.get('success_rate', 0):.1f}%")
            
        else:
            print(f"❌ Learning analytics: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Learning analytics: Error - {e}")

def test_retraining_trigger():
    """Test manual retraining trigger."""
    print("\n🔄 Testing Retraining Trigger...")
    
    try:
        response = requests.post(f"{BASE_URL}/learning/trigger-retraining/candidate_matching")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retraining triggered: {data['message']}")
        else:
            print(f"❌ Retraining trigger: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Retraining trigger: Error - {e}")

def simulate_continuous_learning():
    """Simulate continuous learning with multiple feedback cycles."""
    print("\n🔄 Simulating Continuous Learning Cycles...")
    
    for cycle in range(3):
        print(f"\n--- Learning Cycle {cycle + 1} ---")
        
        # Submit multiple feedback items
        for i in range(5):
            # Vary scores slightly to simulate real-world variation
            base_score = 0.8 + (np.random.random() - 0.5) * 0.2  # 0.7 to 0.9
            
            feedback = generate_feedback_data(
                "candidate_match_quality",
                base_score,
                {
                    "skill_match_score": 0.8 + np.random.random() * 0.2,
                    "experience_match_score": 0.7 + np.random.random() * 0.3,
                    "culture_match_score": 0.6 + np.random.random() * 0.4,
                    "location_match_score": 0.8 + np.random.random() * 0.2,
                    "salary_match_score": 0.7 + np.random.random() * 0.3,
                    "availability_match_score": 0.8 + np.random.random() * 0.2,
                    "communication_score": 0.7 + np.random.random() * 0.3,
                    "technical_assessment_score": 0.8 + np.random.random() * 0.2,
                    "client_preference_score": 0.7 + np.random.random() * 0.3,
                    "market_demand_score": 0.6 + np.random.random() * 0.4
                }
            )
            
            response = requests.post(f"{BASE_URL}/learning/feedback", json=feedback)
            if response.status_code == 200:
                print(f"   ✅ Feedback {i+1} submitted")
            else:
                print(f"   ❌ Feedback {i+1} failed: {response.status_code}")
        
        # Wait for processing
        print("   ⏳ Waiting for feedback processing...")
        time.sleep(2)
        
        # Check learning signals
        response = requests.get(f"{BASE_URL}/learning/signals")
        if response.status_code == 200:
            data = response.json()
            signals = data.get("signals", [])
            print(f"   🧠 {len(signals)} learning signals detected")

def main():
    """Run all continuous learning tests."""
    print("🚀 Starting Continuous Learning System Tests")
    print("=" * 50)
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ API is not responding. Please start the backend server.")
            return
        print("✅ API is running")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("Please start the backend server with: python -m uvicorn src.github_talent_intelligence.api:app --reload")
        return
    
    # Run tests
    test_feedback_submission()
    test_placement_outcomes()
    test_model_performance()
    test_learning_signals()
    test_learning_analytics()
    test_retraining_trigger()
    simulate_continuous_learning()
    
    print("\n" + "=" * 50)
    print("🎉 Continuous Learning System Tests Complete!")
    print("\nNext steps:")
    print("1. Visit http://localhost:3000/learning-analytics to see the dashboard")
    print("2. Submit more feedback to see the system learn")
    print("3. Monitor model performance improvements over time")

if __name__ == "__main__":
    main() 