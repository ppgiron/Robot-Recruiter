#!/usr/bin/env python3
"""
Example Integration with AI Recruiting Application
Demonstrates how to use the GitHub Talent Intelligence Platform
with AI recruiting systems.
"""

import json
import os
from recruiting_integration import RecruitingIntegration


def main():
    """Example integration with AI recruiting application."""
    
    # Initialize the recruiting integration
    # You can set GITHUB_TOKEN environment variable or pass it directly
    integration = RecruitingIntegration()
    
    print("🤖 AI Recruiting Integration Example")
    print("=" * 50)
    
    # Example 1: Discover talent from specific organizations
    print("\n1. Discovering talent from blockchain organizations...")
    
    talent_results = integration.discover_talent(
        organizations=['ChainSafe', 'ethereum', 'filecoin-project'],
        skills=['Python', 'Go', 'Rust', 'DevOps', 'Blockchain'],
        min_contributions=20,
        min_followers=100
    )
    
    print(f"Found {len(talent_results['candidates'])} qualified candidates")
    
    # Show top 5 candidates
    print("\nTop 5 candidates:")
    for i, candidate in enumerate(talent_results['candidates'][:5], 1):
        print(f"{i}. {candidate['name'] or candidate['login']}")
        print(f"   Score: {candidate['talent_score']:.2f}")
        print(f"   Skills: {', '.join(candidate['skills'])}")
        print(f"   Contributions: {candidate['contributions']}")
        print()
    
    # Example 2: Assess a specific candidate
    print("\n2. Assessing a specific candidate...")
    
    # You can replace this with any GitHub username
    candidate_assessment = integration.assess_candidate("example_user")
    
    if 'error' not in candidate_assessment:
        print(f"Candidate: {candidate_assessment['user']['login']}")
        print(f"Expertise Score: {candidate_assessment['expertise_score']:.2f}")
        print(f"Skills: {', '.join(candidate_assessment['skills'])}")
        print(f"Recommendations: {', '.join(candidate_assessment['recommendations'])}")
    else:
        print("Candidate not found or error occurred")
    
    # Example 3: Match candidates to a specific role
    print("\n3. Matching candidates to a DevOps Engineer role...")
    
    role_requirements = {
        'title': 'DevOps Engineer',
        'skills': ['Python', 'Docker', 'Kubernetes', 'Terraform'],
        'experience_level': 'mid',
        'location': 'Remote'
    }
    
    matches = integration.match_candidates_to_role(
        role_requirements,
        talent_results['candidates'][:10]  # Top 10 candidates
    )
    
    print(f"Found {len(matches)} matches for DevOps Engineer role")
    
    for i, match in enumerate(matches[:3], 1):
        candidate = match['candidate']
        print(f"\n{i}. {candidate['name'] or candidate['login']}")
        print(f"   Match Score: {match['match_score']:.2f}")
        print(f"   Strengths: {', '.join(match['strengths'])}")
        if match['gaps']:
            print(f"   Gaps: {', '.join(match['gaps'])}")
    
    # Example 4: Generate reports for recruiting team
    print("\n4. Generating talent report...")
    
    report_html = integration.generate_talent_report(talent_results, 'html')
    
    # Save report
    with open('talent_report.html', 'w') as f:
        f.write(report_html)
    
    print("Talent report saved to talent_report.html")
    
    # Example 5: Export for ATS integration
    print("\n5. Exporting data for ATS integration...")
    
    ats_data = integration.export_for_ats(talent_results['candidates'][:5], 'generic')
    
    with open('ats_export.json', 'w') as f:
        json.dump(ats_data, f, indent=2)
    
    print("ATS export saved to ats_export.json")
    
    # Example 6: Integration with AI recruiting workflow
    print("\n6. AI Recruiting Workflow Integration...")
    
    # Simulate AI recruiting workflow
    ai_recruiting_workflow(talent_results, integration)


def ai_recruiting_workflow(talent_results, integration):
    """Simulate integration with AI recruiting workflow."""
    
    print("🤖 AI Recruiting Workflow:")
    print("-" * 30)
    
    # Step 1: AI-powered candidate screening
    print("Step 1: AI-powered candidate screening...")
    
    # Filter candidates based on AI criteria
    ai_screened_candidates = []
    for candidate in talent_results['candidates']:
        # AI screening criteria (example)
        if (candidate['talent_score'] > 0.6 and 
            len(candidate['skills']) >= 3 and
            candidate['contributions'] > 50):
            ai_screened_candidates.append(candidate)
    
    print(f"AI screened {len(ai_screened_candidates)} candidates from {len(talent_results['candidates'])} total")
    
    # Step 2: Role-specific matching
    print("\nStep 2: Role-specific matching...")
    
    roles = [
        {
            'title': 'Senior Blockchain Developer',
            'skills': ['Rust', 'Go', 'Blockchain', 'Protocol'],
            'experience_level': 'senior',
            'priority': 'high'
        },
        {
            'title': 'DevOps Engineer',
            'skills': ['Docker', 'Kubernetes', 'Terraform', 'Python'],
            'experience_level': 'mid',
            'priority': 'medium'
        },
        {
            'title': 'Security Engineer',
            'skills': ['Security', 'Cryptography', 'Python', 'Go'],
            'experience_level': 'senior',
            'priority': 'high'
        }
    ]
    
    role_matches = {}
    for role in roles:
        matches = integration.match_candidates_to_role(role, ai_screened_candidates)
        role_matches[role['title']] = matches[:5]  # Top 5 matches per role
    
    # Step 3: Generate AI insights
    print("\nStep 3: Generating AI insights...")
    
    insights = {
        'market_analysis': {
            'total_candidates': len(talent_results['candidates']),
            'high_quality_candidates': len(ai_screened_candidates),
            'skill_distribution': analyze_skill_distribution(ai_screened_candidates),
            'location_distribution': analyze_location_distribution(ai_screened_candidates)
        },
        'role_recommendations': {
            role['title']: {
                'candidate_count': len(matches),
                'avg_match_score': sum(m['match_score'] for m in matches) / len(matches) if matches else 0,
                'top_candidates': [m['candidate']['login'] for m in matches[:3]]
            }
            for role, matches in role_matches.items()
        }
    }
    
    # Step 4: Export for AI recruiting platform
    print("\nStep 4: Exporting for AI recruiting platform...")
    
    ai_platform_data = {
        'candidates': ai_screened_candidates,
        'role_matches': role_matches,
        'insights': insights,
        'metadata': {
            'source': 'GitHub Talent Intelligence',
            'analysis_date': talent_results['summary'].get('analysis_date', ''),
            'ai_screening_criteria': {
                'min_talent_score': 0.6,
                'min_skills': 3,
                'min_contributions': 50
            }
        }
    }
    
    with open('ai_recruiting_data.json', 'w') as f:
        json.dump(ai_platform_data, f, indent=2, default=str)
    
    print("AI recruiting data exported to ai_recruiting_data.json")
    
    # Step 5: Generate actionable insights
    print("\nStep 5: Actionable insights for recruiters:")
    
    print(f"📊 Market Overview:")
    print(f"   - {insights['market_analysis']['total_candidates']} total candidates discovered")
    print(f"   - {insights['market_analysis']['high_quality_candidates']} high-quality candidates")
    
    print(f"\n🎯 Role Recommendations:")
    for role_title, data in insights['role_recommendations'].items():
        print(f"   - {role_title}: {data['candidate_count']} candidates (avg score: {data['avg_match_score']:.2f})")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Review top candidates for each role")
    print(f"   2. Schedule technical assessments")
    print(f"   3. Initiate outreach campaigns")
    print(f"   4. Monitor candidate engagement")


def analyze_skill_distribution(candidates):
    """Analyze skill distribution among candidates."""
    skill_counts = {}
    for candidate in candidates:
        for skill in candidate.get('skills', []):
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
    
    return dict(sorted(skill_counts.items(), key=lambda x: x[1], reverse=True))


def analyze_location_distribution(candidates):
    """Analyze location distribution among candidates."""
    location_counts = {}
    for candidate in candidates:
        location = candidate.get('location', 'Unknown')
        location_counts[location] = location_counts.get(location, 0) + 1
    
    return dict(sorted(location_counts.items(), key=lambda x: x[1], reverse=True))


if __name__ == '__main__':
    main() 