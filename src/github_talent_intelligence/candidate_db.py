"""
Database models for storing candidate and repository analysis data.
"""

from datetime import datetime, UTC
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class Repository(Base):
    """Repository information."""
    __tablename__ = 'repositories'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    language = Column(String(100))
    classification = Column(String(100))
    private = Column(Boolean, default=False)
    html_url = Column(String(500))
    git_url = Column(String(500))
    clone_url = Column(String(500))
    homepage = Column(String(500))
    size = Column(Integer)
    stargazers_count = Column(Integer)
    watchers_count = Column(Integer)
    forks_count = Column(Integer)
    open_issues_count = Column(Integer)
    license_info = Column(JSON)
    owner_login = Column(String(255))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    pushed_at = Column(DateTime)
    analysis_date = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    contributors = relationship("Contributor", back_populates="repository")
    skills = relationship("RepositorySkill", back_populates="repository")


class Contributor(Base):
    """Contributor information."""
    __tablename__ = 'contributors'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey('repositories.id'))
    github_id = Column(Integer, nullable=False)
    login = Column(String(255), nullable=False)
    name = Column(String(255))
    email = Column(String(255))
    bio = Column(Text)
    location = Column(String(255))
    company = Column(String(255))
    blog = Column(String(500))
    twitter_username = Column(String(255))
    hireable = Column(Boolean)
    public_repos = Column(Integer)
    public_gists = Column(Integer)
    followers = Column(Integer)
    following = Column(Integer)
    contributions = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))
    analysis_date = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    repository = relationship("Repository", back_populates="contributors")
    skills = relationship("ContributorSkill", back_populates="contributor")
    roles = relationship("ContributorRole", back_populates="contributor")


class ContributorRole(Base):
    """Contributor role classifications."""
    __tablename__ = 'contributor_roles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contributor_id = Column(UUID(as_uuid=True), ForeignKey('contributors.id'))
    role_type = Column(String(50), nullable=False)  # 'code', 'docs', 'test', etc.
    score = Column(Float, nullable=False)
    confidence = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    contributor = relationship("Contributor", back_populates="roles")


class ContributorSkill(Base):
    """Contributor skills and expertise."""
    __tablename__ = 'contributor_skills'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contributor_id = Column(UUID(as_uuid=True), ForeignKey('contributors.id'))
    skill_name = Column(String(255), nullable=False)
    skill_category = Column(String(100))  # 'language', 'framework', 'tool', etc.
    confidence_score = Column(Float)
    evidence = Column(Text)  # How this skill was detected
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    contributor = relationship("Contributor", back_populates="skills")


class RepositorySkill(Base):
    """Repository-level skills and technologies."""
    __tablename__ = 'repository_skills'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey('repositories.id'))
    skill_name = Column(String(255), nullable=False)
    skill_category = Column(String(100))
    usage_count = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    repository = relationship("Repository", back_populates="skills")


class AnalysisSession(Base):
    """Analysis session metadata."""
    __tablename__ = 'analysis_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_name = Column(String(255))
    analysis_type = Column(String(100))  # 'repository', 'organization', 'user'
    target = Column(String(255))  # repo name, org name, or username
    status = Column(String(50))  # 'running', 'completed', 'failed'
    started_at = Column(DateTime, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime)
    repositories_analyzed = Column(Integer, default=0)
    contributors_found = Column(Integer, default=0)
    errors = Column(Text)
    config_used = Column(JSON)
    
    # Relationships
    repositories = relationship("Repository", secondary="session_repositories")


class SessionRepository(Base):
    """Many-to-many relationship between sessions and repositories."""
    __tablename__ = 'session_repositories'
    
    session_id = Column(UUID(as_uuid=True), ForeignKey('analysis_sessions.id'), primary_key=True)
    repository_id = Column(UUID(as_uuid=True), ForeignKey('repositories.id'), primary_key=True)


class CandidateProfile(Base):
    """Aggregated candidate profile from multiple repositories."""
    __tablename__ = 'candidate_profiles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_id = Column(Integer, unique=True, nullable=False)
    login = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    email = Column(String(255))
    bio = Column(Text)
    location = Column(String(255))
    company = Column(String(255))
    blog = Column(String(500))
    twitter_username = Column(String(255))
    hireable = Column(Boolean)
    public_repos = Column(Integer)
    public_gists = Column(Integer)
    followers = Column(Integer)
    following = Column(Integer)
    total_contributions = Column(Integer, default=0)
    repositories_contributed = Column(Integer, default=0)
    primary_classifications = Column(JSON)  # Most common repo classifications
    top_skills = Column(JSON)  # Aggregated skills
    expertise_score = Column(Float)
    last_updated = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    contributions = relationship("CandidateContribution", back_populates="candidate")


class CandidateContribution(Base):
    """Individual contributions by candidates to repositories."""
    __tablename__ = 'candidate_contributions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey('candidate_profiles.id'))
    repository_id = Column(UUID(as_uuid=True), ForeignKey('repositories.id'))
    contributions = Column(Integer, default=0)
    first_contribution = Column(DateTime)
    last_contribution = Column(DateTime)
    roles = Column(JSON)  # Role scores for this repo
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    candidate = relationship("CandidateProfile", back_populates="contributions")
    repository = relationship("Repository")


class DatabaseManager:
    """Database manager for candidate data."""
    
    def __init__(self, database_url):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()
    
    def save_repository_analysis(self, repo_data, contributors_data, session_name=None):
        """Save repository analysis results to database."""
        session = self.get_session()
        try:
            # Create analysis session
            analysis_session = AnalysisSession(
                session_name=session_name or f"Analysis_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
                analysis_type="repository",
                target=repo_data.get('full_name'),
                status="completed",
                completed_at=datetime.now(UTC),
                repositories_analyzed=1,
                contributors_found=len(contributors_data)
            )
            session.add(analysis_session)
            session.flush()
            
            # Save repository
            repo = Repository(
                full_name=repo_data.get('full_name'),
                name=repo_data.get('name'),
                description=repo_data.get('description'),
                language=repo_data.get('language'),
                classification=repo_data.get('classification'),
                private=repo_data.get('private', False),
                html_url=repo_data.get('html_url'),
                git_url=repo_data.get('git_url'),
                clone_url=repo_data.get('clone_url'),
                homepage=repo_data.get('homepage'),
                size=repo_data.get('size'),
                stargazers_count=repo_data.get('stargazers_count'),
                watchers_count=repo_data.get('watchers_count'),
                forks_count=repo_data.get('forks_count'),
                open_issues_count=repo_data.get('open_issues_count'),
                license_info=repo_data.get('license'),
                owner_login=repo_data.get('owner', {}).get('login') if repo_data.get('owner') else None,
                created_at=datetime.fromisoformat(repo_data.get('created_at').replace('Z', '+00:00')) if repo_data.get('created_at') else None,
                updated_at=datetime.fromisoformat(repo_data.get('updated_at').replace('Z', '+00:00')) if repo_data.get('updated_at') else None,
                pushed_at=datetime.fromisoformat(repo_data.get('pushed_at').replace('Z', '+00:00')) if repo_data.get('pushed_at') else None
            )
            session.add(repo)
            session.flush()
            
            # Link repository to session
            session_repo = SessionRepository(
                session_id=analysis_session.id,
                repository_id=repo.id
            )
            session.add(session_repo)
            
            # Save contributors
            for contrib_data in contributors_data:
                contributor = Contributor(
                    repository_id=repo.id,
                    github_id=contrib_data.get('id'),
                    login=contrib_data.get('login'),
                    name=contrib_data.get('name'),
                    email=contrib_data.get('email'),
                    bio=contrib_data.get('bio'),
                    location=contrib_data.get('location'),
                    company=contrib_data.get('company'),
                    blog=contrib_data.get('blog'),
                    twitter_username=contrib_data.get('twitter_username'),
                    hireable=contrib_data.get('hireable'),
                    public_repos=contrib_data.get('public_repos'),
                    public_gists=contrib_data.get('public_gists'),
                    followers=contrib_data.get('followers'),
                    following=contrib_data.get('following'),
                    contributions=contrib_data.get('contributions'),
                    created_at=datetime.fromisoformat(contrib_data.get('created_at').replace('Z', '+00:00')) if contrib_data.get('created_at') else None,
                    updated_at=datetime.fromisoformat(contrib_data.get('updated_at').replace('Z', '+00:00')) if contrib_data.get('updated_at') else None
                )
                session.add(contributor)
                session.flush()
                
                # Save roles
                roles = contrib_data.get('roles', {})
                for role_type, score in roles.items():
                    role = ContributorRole(
                        contributor_id=contributor.id,
                        role_type=role_type,
                        score=float(score)
                    )
                    session.add(role)
                
                # Save skills if available
                skills = contrib_data.get('skills', [])
                for skill in skills:
                    skill_obj = ContributorSkill(
                        contributor_id=contributor.id,
                        skill_name=skill.get('name'),
                        skill_category=skill.get('category'),
                        confidence_score=skill.get('confidence'),
                        evidence=skill.get('evidence')
                    )
                    session.add(skill_obj)
            
            session.commit()
            return analysis_session.id
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_candidate_profiles(self, limit=100, offset=0):
        """Get candidate profiles with pagination."""
        session = self.get_session()
        try:
            profiles = session.query(CandidateProfile).offset(offset).limit(limit).all()
            return profiles
        finally:
            session.close()
    
    def get_candidate_by_github_id(self, github_id):
        """Get candidate profile by GitHub ID."""
        session = self.get_session()
        try:
            return session.query(CandidateProfile).filter_by(github_id=github_id).first()
        finally:
            session.close()
    
    def search_candidates(self, skills=None, location=None, company=None, classification=None):
        """Search candidates by various criteria."""
        session = self.get_session()
        try:
            query = session.query(CandidateProfile)
            
            if skills:
                # This would need to be implemented with proper skill matching
                pass
            
            if location:
                query = query.filter(CandidateProfile.location.ilike(f"%{location}%"))
            
            if company:
                query = query.filter(CandidateProfile.company.ilike(f"%{company}%"))
            
            if classification:
                query = query.filter(CandidateProfile.primary_classifications.contains([classification]))
            
            return query.all()
        finally:
            session.close() 