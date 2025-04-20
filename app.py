import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

st.set_page_config(
    page_title="GitHub Repo Analyzer",
    page_icon="📊",
    layout="wide"
)

load_dotenv()

# GitHub API token
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
headers = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}

def get_readme_content(owner, repo):
    """Fetching and decoding README content from GitHub repository"""
    try:
        readme_url = f'https://api.github.com/repos/{owner}/{repo}/readme'
        readme_response = requests.get(readme_url, headers=headers)
        
        if readme_response.status_code == 200:
            import base64
            readme_data = readme_response.json()
            content = base64.b64decode(readme_data['content']).decode('utf-8')
            return content
        return None
    except Exception as e:
        st.error(f"Error fetching README: {str(e)}")
        return None

def get_repo_info(repo_url):
    """Extracting owner and repo name from GitHub URL and fetch repository data"""
    try:
        # Parsing URL to get owner and repo
        parts = repo_url.strip('/').split('/')
        owner, repo = parts[-2], parts[-1]
        
        # Fetching repository information
        repo_api_url = f'https://api.github.com/repos/{owner}/{repo}'
        repo_response = requests.get(repo_api_url, headers=headers)
        repo_data = repo_response.json()
        
        if repo_response.status_code != 200:
            st.error(f"Error: {repo_data.get('message', 'Failed to fetch repository data')}")
            return None
        
        # Fetching commit activity
        commits_url = f'{repo_api_url}/stats/commit_activity'
        commits_response = requests.get(commits_url, headers=headers)
        commits_data = commits_response.json() if commits_response.status_code == 200 else []
        
        # Fetching contributors
        contributors_url = f'{repo_api_url}/contributors'
        contributors_response = requests.get(contributors_url, headers=headers)
        contributors_data = contributors_response.json() if contributors_response.status_code == 200 else []
        
        # Fetching README content
        readme_content = get_readme_content(owner, repo)
        
        return {
            'repo_data': repo_data,
            'commits_data': commits_data,
            'contributors_data': contributors_data,
            'readme_content': readme_content
        }
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def get_language_stats(repo_data):
    """Extracting language statistics from repository data"""
    if not repo_data.get('languages_url'):
        return {}
    
    languages_response = requests.get(repo_data['languages_url'], headers=headers)
    if languages_response.status_code == 200:
        return languages_response.json()
    return {}

def generate_report(repo_data, commits_data, contributors_data, is_comparison=False):
    """Generating a detailed report for the repository"""
    report = []
    
    # Repository metadata
    report.append(f"Repository Analysis Report for {repo_data['name']}")
    report.append("=" * 50)
    report.append(f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("\nRepository Metadata:")
    report.append("-" * 20)
    report.append(f"Name: {repo_data['name']}")
    report.append(f"Owner: {repo_data['owner']['login']}")
    report.append(f"Description: {repo_data['description'] or 'No description provided'}")
    report.append(f"Stars: {repo_data['stargazers_count']}")
    report.append(f"Forks: {repo_data['forks_count']}")
    report.append(f"Open Issues: {repo_data['open_issues_count']}")
    report.append(f"Watchers: {repo_data['watchers_count']}")
    report.append(f"Created: {datetime.strptime(repo_data['created_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')}")
    report.append(f"Last Updated: {datetime.strptime(repo_data['updated_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')}")
    
    # Top contributors
    report.append("\nTop Contributors:")
    report.append("-" * 20)
    for i, contributor in enumerate(contributors_data[:10], 1):
        report.append(f"{i}. {contributor['login']}: {contributor['contributions']} contributions")
    
    # Weekly commit activity
    report.append("\nWeekly Commit Activity (Last 52 weeks):")
    report.append("-" * 20)
    for i, week in enumerate(commits_data):
        report.append(f"Week {i+1}: {week['total']} commits")
    
    return "\n".join(report)

def display_repo_metrics(repo_data, column):
    """Displaying the repository metrics"""
    with column:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Stars", repo_data['stargazers_count'])
            st.metric("Forks", repo_data['forks_count'])
        with col2:
            st.metric("Issues", repo_data['open_issues_count'])
            st.metric("Watchers", repo_data['watchers_count'])

def display_repo_details(repo_data, col):
    """Displaying repository details"""
    with col:
        st.write(f"**Description:** {repo_data['description'] or 'No description'}")
        st.write(f"**Language:** {repo_data['language'] or 'Not specified'}")
        st.write(f"**Created:** {datetime.strptime(repo_data['created_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y')}")
        st.write(f"**Owner:** {repo_data['owner']['login']}")
        st.write(f"**License:** {repo_data['license']['name'] if repo_data['license'] else 'Not specified'}")
        st.write(f"**Last Updated:** {datetime.strptime(repo_data['updated_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y')}")

def filter_commits_by_timeframe(commits_data, timeframe_weeks):
    """Filtering commit data based on selected timeframe"""
    if not commits_data or timeframe_weeks >= len(commits_data):
        return commits_data
    return commits_data[-timeframe_weeks:]

def plot_commit_activity(commits_data1, commits_data2=None, repo1_name="Repository 1", repo2_name="Repository 2", timeframe="All Time"):
    """Plotting commit activity comparison chart with timeframe filtering"""
    fig = go.Figure()
    
    timeframe_mapping = {
        "Last Week": 1,
        "Last Month": 4,
        "Last 3 Months": 12,
        "Last 6 Months": 26,
        "All Time": 52
    }
    weeks_to_show = timeframe_mapping.get(timeframe, 52)
    
    if commits_data1:
        filtered_data1 = filter_commits_by_timeframe(commits_data1, weeks_to_show)
        weeks = list(range(len(filtered_data1)))
        commits1 = [week['total'] for week in filtered_data1]
        fig.add_trace(go.Scatter(
            x=weeks,
            y=commits1,
            name=repo1_name,
            line=dict(color='#2ecc71')
        ))
    
    if commits_data2:
        filtered_data2 = filter_commits_by_timeframe(commits_data2, weeks_to_show)
        weeks = list(range(len(filtered_data2)))
        commits2 = [week['total'] for week in filtered_data2]
        fig.add_trace(go.Scatter(
            x=weeks,
            y=commits2,
            name=repo2_name,
            line=dict(color='#3498db')
        ))
    
    fig.update_layout(
        title=f"Weekly Commit Activity ({timeframe})",
        xaxis_title="Weeks Ago",
        yaxis_title="Number of Commits",
        showlegend=True
    )
    return fig

def plot_language_comparison(lang_data1, lang_data2=None, repo1_name="Repository 1", repo2_name="Repository 2"):
    """Plotting language usage using pie charts"""
    if lang_data2:
        fig = go.Figure()
        
        if lang_data1:
            total1 = sum(lang_data1.values())
            fig.add_trace(go.Pie(
                labels=list(lang_data1.keys()),
                values=list(lang_data1.values()),
                name=repo1_name,
                domain={'x': [0, 0.45]},
                title=repo1_name,
                textinfo='percent',
                hoverinfo='label+percent',
                marker={'colors': px.colors.qualitative.Set3}
            ))
        
        if lang_data2:
            total2 = sum(lang_data2.values())
            fig.add_trace(go.Pie(
                labels=list(lang_data2.keys()),
                values=list(lang_data2.values()),
                name=repo2_name,
                domain={'x': [0.55, 1]},
                title=repo2_name,
                textinfo='percent',
                hoverinfo='label+percent',
                marker={'colors': px.colors.qualitative.Set3}
            ))
    else:
        fig = go.Figure()
        if lang_data1:
            total1 = sum(lang_data1.values())
            fig.add_trace(go.Pie(
                labels=list(lang_data1.keys()),
                values=list(lang_data1.values()),
                name=repo1_name,
                textinfo='percent',
                hoverinfo='label+percent',
                marker={'colors': px.colors.qualitative.Set3}
            ))
    
    fig.update_layout(
        title="Language Distribution",
        showlegend=True,
        height=500
    )
    return fig

def filter_contributors(contributors_data, username_filter=None):
    """Filtering contributors based on username"""
    if not username_filter:
        return contributors_data[:10]
    
    filtered = [c for c in contributors_data if username_filter.lower() in c['login'].lower()]
    return filtered[:10]

def plot_top_contributors(contributors_data1, contributors_data2=None, repo1_name="Repository 1", repo2_name="Repository 2", username_filter=None):
    """Ploting top contributors comparison chart with username filtering"""
    fig = go.Figure()
    
    if contributors_data1:
        filtered_contributors1 = filter_contributors(contributors_data1, username_filter)
        if filtered_contributors1:
            fig.add_trace(go.Bar(
                x=[c['login'] for c in filtered_contributors1],
                y=[c['contributions'] for c in filtered_contributors1],
                name=repo1_name,
                marker_color='#2ecc71'
            ))
    
    if contributors_data2:
        filtered_contributors2 = filter_contributors(contributors_data2, username_filter)
        if filtered_contributors2:
            fig.add_trace(go.Bar(
                x=[c['login'] for c in filtered_contributors2],
                y=[c['contributions'] for c in filtered_contributors2],
                name=repo2_name,
                marker_color='#3498db'
            ))
    
    title = "Top Contributors"
    if username_filter:
        title += f" (Filtered by: {username_filter})"
    
    fig.update_layout(
        title=title,
        xaxis_title="Contributor",
        yaxis_title="Number of Contributions",
        barmode='group',
        showlegend=True
    )
    return fig

def analyze_single_repo(repo_url):
    """Analyzing and displaying metrics for a single repository"""
    if not repo_url:
        st.info("Enter a GitHub repository URL to analyze its metrics.")
        return
    
    data = get_repo_info(repo_url)
    if not data:
        return
    
    repo_data = data['repo_data']
    
    # Displaying repository information
    st.header("Repository Metrics")
    col1, col2 = st.columns(2)
    
    with col1:
        display_repo_metrics(repo_data, col1)
    with col2:
        display_repo_details(repo_data, col2)
    
    report = generate_report(repo_data, data['commits_data'], data['contributors_data'])
    st.download_button(
        label="📥 Download Analysis Report",
        data=report,
        file_name=f"{repo_data['name']}_analysis_report.txt",
        mime="text/plain"
    )
    
    # Getting language statistics
    lang_data = get_language_stats(repo_data)
    
    # Visualizations
    st.header("Analysis")
    
    # Commit activity with timeframe selection
    st.subheader("Commit Activity")
    timeframe = st.selectbox(
        "Select Timeframe:",
        ["Last Week", "Last Month", "Last 3 Months", "Last 6 Months", "All Time"],
        index=4
    )
    st.plotly_chart(
        plot_commit_activity(
            data['commits_data'],
            repo1_name=repo_data['name'],
            timeframe=timeframe
        ),
        use_container_width=True
    )
    
    # Language distribution
    st.plotly_chart(
        plot_language_comparison(
            lang_data,
            repo1_name=repo_data['name']
        ),
        use_container_width=True
    )
    
    # Contributors with username filter
    st.subheader("Contributors")
    username_filter = st.text_input(
        "Filter contributors by username:",
        placeholder="Enter username or leave empty for top 10"
    )
    st.plotly_chart(
        plot_top_contributors(
            data['contributors_data'],
            repo1_name=repo_data['name'],
            username_filter=username_filter
        ),
        use_container_width=True
    )
    
    # README preview
    if data['readme_content']:
        st.markdown("---")
        st.header("📖 README Preview")
        preview_length = 1000
        readme_content = data['readme_content']
        
        if len(readme_content) > preview_length:
            st.markdown(readme_content[:preview_length] + "...")
            with st.expander("Read more"):
                st.markdown(readme_content)
        else:
            st.markdown(readme_content)

def analyze_compare_repos(repo_url1, repo_url2):
    """Comparing and displaying metrics for two repositories"""
    if not repo_url1 or not repo_url2:
        st.info("Please enter both repository URLs for comparison.")
        return
    
    # Getting data for both repositories
    data1 = get_repo_info(repo_url1)
    data2 = get_repo_info(repo_url2)
    
    if not data1 or not data2:
        return
    
    # Displaying repository information
    st.header("Repository Metrics")
    col1, col2 = st.columns(2)
    
    # Displaying metrics for first repository
    with col1:
        st.subheader(f"📊 {data1['repo_data']['name']}")
        display_repo_metrics(data1['repo_data'], col1)
        display_repo_details(data1['repo_data'], col1)

        report1 = generate_report(data1['repo_data'], data1['commits_data'], data1['contributors_data'], True)
        st.download_button(
            label=f"📥 Download {data1['repo_data']['name']} Report",
            data=report1,
            file_name=f"{data1['repo_data']['name']}_analysis_report.txt",
            mime="text/plain"
        )
    
    # Displaying metrics for second repository
    with col2:
        st.subheader(f"📊 {data2['repo_data']['name']}")
        display_repo_metrics(data2['repo_data'], col2)
        display_repo_details(data2['repo_data'], col2)
        report2 = generate_report(data2['repo_data'], data2['commits_data'], data2['contributors_data'], True)
        st.download_button(
            label=f"📥 Download {data2['repo_data']['name']} Report",
            data=report2,
            file_name=f"{data2['repo_data']['name']}_analysis_report.txt",
            mime="text/plain"
        )
    
    # Getting language statistics
    lang_data1 = get_language_stats(data1['repo_data'])
    lang_data2 = get_language_stats(data2['repo_data'])
    
    # Visualizations
    st.header("Comparative Analysis")
    
    # Commit activity comparison with timeframe selection
    st.subheader("Commit Activity Comparison")
    timeframe = st.selectbox(
        "Select Timeframe:",
        ["Last Week", "Last Month", "Last 3 Months", "Last 6 Months", "All Time"],
        index=4
    )
    st.plotly_chart(
        plot_commit_activity(
            data1['commits_data'],
            data2['commits_data'],
            data1['repo_data']['name'],
            data2['repo_data']['name'],
            timeframe=timeframe
        ),
        use_container_width=True
    )
    
    # Language distribution comparison
    st.plotly_chart(
        plot_language_comparison(
            lang_data1,
            lang_data2,
            data1['repo_data']['name'],
            data2['repo_data']['name']
        ),
        use_container_width=True
    )
    
    # Contributors comparison with username filter
    st.subheader("Contributors Comparison")
    username_filter = st.text_input(
        "Filter contributors by username:",
        placeholder="Enter username or leave empty for top 10"
    )
    st.plotly_chart(
        plot_top_contributors(
            data1['contributors_data'],
            data2['contributors_data'],
            data1['repo_data']['name'],
            data2['repo_data']['name'],
            username_filter=username_filter
        ),
        use_container_width=True
    )

def main():
    st.title("📊 GitHub Repo Analyzer")
    
    # Sidebar for token input and mode selection
    with st.sidebar:
        # GitHub token input
        st.markdown("### GitHub Token (Optional)")
        token = st.text_input(
            "Enter your GitHub Personal Access Token:",
            type="password",
            help="A token allows higher API rate limits. Leave empty to use default limits.",
            placeholder="ghp_xxxxxxxxxxxx"
        )
        if token:
            os.environ['GITHUB_TOKEN'] = token
            st.success("✅ Token set successfully!")
        
        st.markdown("---")
        
        mode = st.radio(
            "Select Analysis Mode:",
            ["Single Repository", "Repository Comparison"]
        )
    
    # Single repository analysis
    if mode == "Single Repository":
        repo_url = st.text_input(
            "Enter Repository URL:",
            placeholder="https://github.com/owner/repo"
        )
        if repo_url:
            analyze_single_repo(repo_url)
    
    # Repository comparison
    else:
        col1, col2 = st.columns(2)
        with col1:
            repo_url1 = st.text_input(
                "Enter First Repository URL:",
                placeholder="https://github.com/owner/repo"
            )
        with col2:
            repo_url2 = st.text_input(
                "Enter Second Repository URL:",
                placeholder="https://github.com/owner/repo"
            )
        if repo_url1 and repo_url2:
            analyze_compare_repos(repo_url1, repo_url2)
    
    with st.sidebar:
        if not (token or GITHUB_TOKEN):
            st.warning("⚠️ No GitHub token found. Some API requests might be rate-limited.")
        
        st.markdown("---")
        st.markdown("### How to Use")
        if mode == "Single Repository":
            st.markdown("""
                1. Enter a GitHub repository URL
                2. View detailed metrics and visualizations
                3. Analyze commit patterns and language usage
            """)
        else:
            st.markdown("""
                1. Enter two GitHub repository URLs
                2. Compare metrics side by side
                3. Analyze differences in:
                   - Commit patterns
                   - Language usage
                   - Contributor activity
            """)
    


if __name__ == "__main__":
    main()
