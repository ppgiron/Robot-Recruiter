import sys
import os
import uuid
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from github_talent_intelligence.db import get_engine
from github_talent_intelligence.candidate_db import CandidateProfile
from github_talent_intelligence.embedding_service import embedding_service

from sqlalchemy import Table, MetaData

VECTOR_DIM = 384

# Table name must match migration
CANDIDATE_EMBEDDINGS_TABLE = 'candidate_embeddings'


def build_candidate_text(candidate: CandidateProfile) -> str:
    # Concatenate relevant fields for embedding
    fields = [
        candidate.name or '',
        candidate.bio or '',
        candidate.location or '',
        str(candidate.primary_classifications or ''),
        str(candidate.top_skills or ''),
        str(candidate.company or ''),
        str(candidate.expertise_score or ''),
    ]
    return ' '.join(fields)


def main():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    metadata = MetaData()
    metadata.reflect(bind=engine)
    embeddings_table = Table(CANDIDATE_EMBEDDINGS_TABLE, metadata, autoload_with=engine)

    candidates = session.query(CandidateProfile).all()
    print(f"Found {len(candidates)} candidates to embed.")

    for idx, candidate in enumerate(candidates, 1):
        text = build_candidate_text(candidate)
        emb = embedding_service.generate_embedding(text)
        emb_list = emb.tolist()
        # Upsert (insert or update)
        stmt = insert(embeddings_table).values(
            id=uuid.uuid4(),
            candidate_id=candidate.id,
            embedding=emb_list,
            created_at=datetime.utcnow(),
            meta={"source": "batch_script"}
        ).on_conflict_do_update(
            index_elements=['candidate_id'],
            set_={
                'embedding': emb_list,
                'created_at': datetime.utcnow(),
                'meta': {"source": "batch_script"}
            }
        )
        session.execute(stmt)
        if idx % 10 == 0 or idx == len(candidates):
            print(f"Processed {idx}/{len(candidates)} candidates...")
    session.commit()
    print("✅ Batch embedding complete.")

if __name__ == "__main__":
    main() 