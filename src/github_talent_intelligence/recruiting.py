"""
AI Recruiting Integration Module
Specialized functions for integrating GitHub talent intelligence with AI recruiting platforms.
"""

import json
import pandas as pd
from typing import List, Dict, Optional, Any
from dataclasses import asdict
from . import TalentAnalyzer, Repository, Contributor


class RecruitingIntegration:
    """
    Integration layer for AI recruiting applications.
    Provides specialized functions for talent discovery, assessment, and matching.
    """
    
    def __init__(self, github_token: Optional[str] = None, config_path: Optional[str] = None):
        """
        Initialize the recruiting integration.
        
        Args:
            github_token: GitHub API token
            config_path: Path to configuration file
        """
        self.analyzer = TalentAnalyzer(github_token, config_path)
        
    def discover_talent(self, 
                       organizations: Optional[List[str]] = None,
                       repositories: Optional[List[str]] = None,
                       skills: Optional[List[str]] = None,
                       min_contributions: int = 10,
                       min_followers: int = 50) -> Dict[str, Any]:
        """
        Discover talented contributors from GitHub.
        
        Args:
            organizations: List of GitHub organizations to analyze
            repositories: List of specific repositories to analyze
            skills: Skills to filter for
            min_contributions: Minimum contributions required
            min_followers: Minimum followers required
            
        Returns:
            Dictionary with discovered talent and insights
        """
        all_repositories = []
        
        # Analyze organizations
        if organizations:
            for org in organizations:
                print(f"Analyzing organization: {org}")
                org_repos = self.analyzer.analyze_organization(org)
                all_repositories.extend(org_repos)
        
        # Analyze specific repositories
        if repositories:
            for repo in repositories:
                print(f"Analyzing repository: {repo}")
                repo_data = self.analyzer._get_repo_details(repo)
                if repo_data:
                    analyzed_repo = self.analyzer.analyze_repositories([repo_data])[0]
                    all_repositories.append(analyzed_repo)
        
        # Extract and filter contributors
        candidates = self._extract_candidates(all_repositories, skills, min_contributions, min_followers)
        
        # Score candidates
        scored_candidates = self._score_candidates(candidates)
        
        return {
            'candidates': scored_candidates,
            'summary': {
                'total_candidates': len(scored_candidates),
                'organizations_analyzed': len(organizations) if organizations else 0,
                'repositories_analyzed': len(all_repositories),
                'skills_filtered': skills or []
            }
        }
    
    def assess_candidate(self, username: str) -> Dict[str, Any]:
        """
        Perform comprehensive assessment of a specific candidate.
        
        Args:
            username: GitHub username to assess
            
        Returns:
            Detailed candidate assessment
        """
        # Get user details
        user_data = self.analyzer._get_user_details(username)
        if not user_data:
            return {'error': 'User not found'}
        
        # Get user's repositories
        user_repos = self.analyzer._get_user_repos(username)
        analyzed_repos = self.analyzer.analyze_repositories(user_repos)
        
        # Get repositories where user is a contributor
        contributor_repos = self._get_contributor_repos(username)
        
        # Analyze skills and expertise
        skills = self._analyze_user_skills(user_data, analyzed_repos)
        expertise_score = self._calculate_user_expertise(user_data, analyzed_repos, contributor_repos)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(user_data, skills, expertise_score)
        
        return {
            'user': user_data,
            'skills': skills,
            'expertise_score': expertise_score,
            'repositories': {
                'owned': [self._repo_to_dict(repo) for repo in analyzed_repos],
                'contributed_to': contributor_repos
            },
            'recommendations': recommendations,
            'assessment_date': pd.Timestamp.now().isoformat()
        }
    
    def match_candidates_to_role(self, 
                                role_requirements: Dict[str, Any],
                                candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Match candidates to a specific role based on requirements.
        
        Args:
            role_requirements: Dictionary with role requirements
            candidates: List of candidate assessments
            
        Returns:
            Ranked list of matched candidates
        """
        matches = []
        
        for candidate in candidates:
            match_score = self._calculate_role_match(role_requirements, candidate)
            if match_score > 0:
                matches.append({
                    'candidate': candidate,
                    'match_score': match_score,
                    'strengths': self._identify_strengths(role_requirements, candidate),
                    'gaps': self._identify_gaps(role_requirements, candidate)
                })
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matches
    
    def generate_talent_report(self, 
                              analysis_results: Dict[str, Any],
                              output_format: str = 'json') -> str:
        """
        Generate a comprehensive talent report for recruiting teams.
        
        Args:
            analysis_results: Results from talent discovery
            output_format: Output format ('json', 'csv', 'html')
            
        Returns:
            Generated report content
        """
        if output_format == 'json':
            return json.dumps(analysis_results, indent=2, default=str)
        
        elif output_format == 'csv':
            return self._generate_csv_report(analysis_results)
        
        elif output_format == 'html':
            return self._generate_html_report(analysis_results)
        
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def export_for_ats(self, candidates: List[Dict[str, Any]], ats_type: str = 'generic') -> Dict[str, Any]:
        """
        Export candidate data in format suitable for Applicant Tracking Systems.
        
        Args:
            candidates: List of candidate data
            ats_type: Type of ATS ('generic', 'workday', 'bamboo', etc.)
            
        Returns:
            ATS-formatted candidate data
        """
        if ats_type == 'generic':
            return self._export_generic_ats(candidates)
        elif ats_type == 'workday':
            return self._export_workday_ats(candidates)
        elif ats_type == 'bamboo':
            return self._export_bamboo_ats(candidates)
        else:
            raise ValueError(f"Unsupported ATS type: {ats_type}")
    
    # Private helper methods
    
    def _extract_candidates(self, 
                           repositories: List[Repository],
                           skills: Optional[List[str]],
                           min_contributions: int,
                           min_followers: int) -> List[Dict[str, Any]]:
        """Extract and filter candidates from repositories."""
        candidates = {}
        
        for repo in repositories:
            for contributor in repo.contributors:
                if contributor.login in candidates:
                    # Merge data from multiple repositories
                    existing = candidates[contributor.login]
                    existing['contributions'] += contributor.contributions
                    existing['repositories'].append(repo.full_name)
                else:
                    # Filter by criteria
                    if (contributor.contributions >= min_contributions and 
                        contributor.followers >= min_followers):
                        
                        candidates[contributor.login] = {
                            'login': contributor.login,
                            'name': contributor.name,
                            'bio': contributor.bio,
                            'location': contributor.location,
                            'company': contributor.company,
                            'contributions': contributor.contributions,
                            'followers': contributor.followers,
                            'public_repos': contributor.public_repos,
                            'repositories': [repo.full_name],
                            'skills': contributor.skills or [],
                            'expertise_score': contributor.expertise_score
                        }
        
        # Filter by skills if specified
        if skills:
            filtered_candidates = {}
            for login, candidate in candidates.items():
                candidate_skills = [s.lower() for s in candidate['skills']]
                if any(skill.lower() in candidate_skills for skill in skills):
                    filtered_candidates[login] = candidate
            return list(filtered_candidates.values())
        
        return list(candidates.values())
    
    def _score_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score candidates based on various factors."""
        for candidate in candidates:
            score = 0.0
            
            # Contribution score (40%)
            contrib_score = min(candidate['contributions'] / 100, 1.0)
            score += contrib_score * 0.4
            
            # Follower score (20%)
            follower_score = min(candidate['followers'] / 1000, 1.0)
            score += follower_score * 0.2
            
            # Repository diversity score (20%)
            repo_diversity = min(len(candidate['repositories']) / 10, 1.0)
            score += repo_diversity * 0.2
            
            # Skills score (20%)
            skills_score = min(len(candidate['skills']) / 5, 1.0)
            score += skills_score * 0.2
            
            candidate['talent_score'] = score
        
        # Sort by talent score
        candidates.sort(key=lambda x: x['talent_score'], reverse=True)
        return candidates
    
    def _get_contributor_repos(self, username: str) -> List[Dict[str, Any]]:
        """Get repositories where user is a contributor."""
        # This would require additional API calls to find repositories
        # where the user is a contributor but not the owner
        # For now, return empty list
        return []
    
    def _analyze_user_skills(self, user_data: Dict[str, Any], repositories: List[Repository]) -> List[str]:
        """Analyze user skills based on profile and repositories."""
        skills = []
        
        # Extract skills from bio
        bio = user_data.get('bio', '').lower()
        skill_keywords = ['python', 'javascript', 'go', 'rust', 'java', 'c++', 'devops', 'blockchain', 'security']
        for skill in skill_keywords:
            if skill in bio:
                skills.append(skill.title())
        
        # Extract skills from repository languages
        languages = set()
        for repo in repositories:
            if repo.language:
                languages.add(repo.language)
        
        skills.extend(list(languages))
        
        return list(set(skills))  # Remove duplicates
    
    def _calculate_user_expertise(self, 
                                 user_data: Dict[str, Any],
                                 owned_repos: List[Repository],
                                 contributor_repos: List[Dict[str, Any]]) -> float:
        """Calculate user expertise score."""
        score = 0.0
        
        # Base score from public repos
        score += min(user_data.get('public_repos', 0) / 50, 1.0) * 0.3
        
        # Follower score
        score += min(user_data.get('followers', 0) / 1000, 1.0) * 0.2
        
        # Repository quality score
        total_stars = sum(repo.stargazers_count for repo in owned_repos)
        score += min(total_stars / 1000, 1.0) * 0.3
        
        # Contribution diversity
        contrib_diversity = min(len(contributor_repos) / 20, 1.0)
        score += contrib_diversity * 0.2
        
        return min(score, 1.0)
    
    def _generate_recommendations(self, 
                                 user_data: Dict[str, Any],
                                 skills: List[str],
                                 expertise_score: float) -> List[str]:
        """Generate recommendations for the candidate."""
        recommendations = []
        
        if expertise_score < 0.5:
            recommendations.append("Consider contributing to more open source projects")
        
        if user_data.get('followers', 0) < 100:
            recommendations.append("Build social presence and engage with the community")
        
        if len(skills) < 3:
            recommendations.append("Diversify technical skills across multiple technologies")
        
        if not user_data.get('blog'):
            recommendations.append("Consider starting a technical blog to showcase expertise")
        
        return recommendations
    
    def _calculate_role_match(self, 
                             requirements: Dict[str, Any],
                             candidate: Dict[str, Any]) -> float:
        """Calculate match score between role requirements and candidate."""
        score = 0.0
        
        # Skills match
        required_skills = requirements.get('skills', [])
        candidate_skills = [s.lower() for s in candidate.get('skills', [])]
        
        if required_skills:
            skills_match = sum(1 for skill in required_skills 
                             if skill.lower() in candidate_skills) / len(required_skills)
            score += skills_match * 0.4
        
        # Experience level match
        required_experience = requirements.get('experience_level', 'mid')
        candidate_score = candidate.get('talent_score', 0)
        
        if required_experience == 'junior' and candidate_score >= 0.3:
            score += 0.3
        elif required_experience == 'mid' and candidate_score >= 0.5:
            score += 0.3
        elif required_experience == 'senior' and candidate_score >= 0.7:
            score += 0.3
        
        # Location match (if specified)
        if requirements.get('location') and candidate.get('location'):
            if requirements['location'].lower() in candidate['location'].lower():
                score += 0.2
        
        return min(score, 1.0)
    
    def _identify_strengths(self, requirements: Dict[str, Any], candidate: Dict[str, Any]) -> List[str]:
        """Identify candidate strengths for the role."""
        strengths = []
        
        # High talent score
        if candidate.get('talent_score', 0) > 0.7:
            strengths.append("High overall talent score")
        
        # Strong skills match
        required_skills = requirements.get('skills', [])
        candidate_skills = [s.lower() for s in candidate.get('skills', [])]
        matched_skills = [skill for skill in required_skills 
                         if skill.lower() in candidate_skills]
        if matched_skills:
            strengths.append(f"Strong skills in: {', '.join(matched_skills)}")
        
        # High contribution count
        if candidate.get('contributions', 0) > 100:
            strengths.append("High contribution activity")
        
        return strengths
    
    def _identify_gaps(self, requirements: Dict[str, Any], candidate: Dict[str, Any]) -> List[str]:
        """Identify gaps between requirements and candidate profile."""
        gaps = []
        
        # Missing skills
        required_skills = requirements.get('skills', [])
        candidate_skills = [s.lower() for s in candidate.get('skills', [])]
        missing_skills = [skill for skill in required_skills 
                         if skill.lower() not in candidate_skills]
        if missing_skills:
            gaps.append(f"Missing skills: {', '.join(missing_skills)}")
        
        # Low experience level
        if candidate.get('talent_score', 0) < 0.5:
            gaps.append("May need more experience for senior roles")
        
        return gaps
    
    def _repo_to_dict(self, repo: Repository) -> Dict[str, Any]:
        """Convert repository object to dictionary."""
        return {
            'name': repo.name,
            'full_name': repo.full_name,
            'description': repo.description,
            'language': repo.language,
            'classification': repo.classification,
            'stargazers_count': repo.stargazers_count,
            'forks_count': repo.forks_count
        }
    
    def _generate_csv_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate CSV report."""
        candidates = analysis_results.get('candidates', [])
        if not candidates:
            return "No candidates found"
        
        df = pd.DataFrame(candidates)
        return df.to_csv(index=False)
    
    def _generate_html_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate HTML report."""
        candidates = analysis_results.get('candidates', [])
        summary = analysis_results.get('summary', {})
        
        html = f"""
        <html>
        <head>
            <title>Talent Intelligence Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .candidate {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .score {{ font-weight: bold; color: #007bff; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Talent Intelligence Report</h1>
                <p>Total Candidates: {summary.get('total_candidates', 0)}</p>
                <p>Organizations Analyzed: {summary.get('organizations_analyzed', 0)}</p>
                <p>Repositories Analyzed: {summary.get('repositories_analyzed', 0)}</p>
            </div>
        """
        
        for candidate in candidates[:20]:  # Show top 20
            html += f"""
            <div class="candidate">
                <h3>{candidate.get('name', candidate.get('login', 'Unknown'))}</h3>
                <p><strong>Score:</strong> <span class="score">{candidate.get('talent_score', 0):.2f}</span></p>
                <p><strong>Contributions:</strong> {candidate.get('contributions', 0)}</p>
                <p><strong>Followers:</strong> {candidate.get('followers', 0)}</p>
                <p><strong>Skills:</strong> {', '.join(candidate.get('skills', []))}</p>
                <p><strong>Location:</strong> {candidate.get('location', 'Unknown')}</p>
            </div>
            """
        
        html += "</body></html>"
        return html
    
    def _export_generic_ats(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Export for generic ATS format."""
        return {
            'candidates': [
                {
                    'first_name': candidate.get('name', '').split()[0] if candidate.get('name') else '',
                    'last_name': ' '.join(candidate.get('name', '').split()[1:]) if candidate.get('name') else '',
                    'email': f"{candidate.get('login', '')}@github.com",
                    'phone': '',
                    'location': candidate.get('location', ''),
                    'skills': candidate.get('skills', []),
                    'experience_years': max(1, int(candidate.get('talent_score', 0) * 10)),
                    'source': 'GitHub Talent Intelligence',
                    'notes': f"GitHub: {candidate.get('login', '')}, Score: {candidate.get('talent_score', 0):.2f}"
                }
                for candidate in candidates
            ]
        }
    
    def _export_workday_ats(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Export for Workday ATS format."""
        # Workday-specific format
        return self._export_generic_ats(candidates)  # Simplified for now
    
    def _export_bamboo_ats(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Export for BambooHR ATS format."""
        # BambooHR-specific format
        return self._export_generic_ats(candidates)  # Simplified for now 