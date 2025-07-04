import sys
import os
import uuid
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from github_talent_intelligence.db import get_engine
from github_talent_intelligence.candidate_db import CandidateProfile

from sqlalchemy.orm import sessionmaker

def main():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    demo_candidates = [
        CandidateProfile(
            id=uuid.uuid4(),
            github_id=12345,
            login='alice_dev',
            name='Alice Johnson',
            email='alice@example.com',
            bio='Full-stack developer with 5+ years experience in React, Node.js, and Python',
            location='San Francisco, CA',
            company='TechCorp',
            hireable=True,
            public_repos=25,
            followers=150,
            following=80,
            total_contributions=1250,
            repositories_contributed=15,
            primary_classifications={'web-development': 0.8, 'full-stack': 0.9},
            top_skills=['JavaScript', 'React', 'Node.js', 'Python', 'PostgreSQL'],
            expertise_score=8.5,
            last_updated=datetime.utcnow()
        ),
        CandidateProfile(
            id=uuid.uuid4(),
            github_id=67890,
            login='bob_engineer',
            name='Bob Smith',
            email='bob@example.com',
            bio='Backend engineer specializing in distributed systems and microservices',
            location='New York, NY',
            company='StartupXYZ',
            hireable=True,
            public_repos=18,
            followers=89,
            following=45,
            total_contributions=890,
            repositories_contributed=12,
            primary_classifications={'backend': 0.9, 'distributed-systems': 0.85},
            top_skills=['Go', 'Kubernetes', 'Docker', 'PostgreSQL', 'Redis'],
            expertise_score=9.2,
            last_updated=datetime.utcnow()
        ),
        CandidateProfile(
            id=uuid.uuid4(),
            github_id=11111,
            login='carol_ml',
            name='Carol Chen',
            email='carol@example.com',
            bio='ML engineer with expertise in computer vision and NLP',
            location='Seattle, WA',
            company='AI Labs',
            hireable=True,
            public_repos=32,
            followers=234,
            following=67,
            total_contributions=2100,
            repositories_contributed=28,
            primary_classifications={'machine-learning': 0.95, 'ai': 0.9},
            top_skills=['Python', 'TensorFlow', 'PyTorch', 'OpenCV', 'NLP'],
            expertise_score=9.8,
            last_updated=datetime.utcnow()
        ),
    ]

    session.add_all(demo_candidates)
    session.commit()
    print(f"✅ Seeded {len(demo_candidates)} demo candidates.")

if __name__ == "__main__":
    main()