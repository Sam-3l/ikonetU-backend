from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Q, Count, Max
from .models import Video
from apps.accounts.models import User
from apps.profiles.models import FounderProfile, InvestorProfile
from .serializers import VideoWithFounderSerializer
from thefuzz import fuzz, process
import re


@api_view(['GET'])
@permission_classes([AllowAny])
def search_view(request):
    """Universal search - videos, founders, investors with fuzzy matching"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return Response({
            'videos': [],
            'profiles': [],
            'query': query
        })
    
    # Fuzzy search videos
    all_videos = Video.objects.filter(
        status='active',
        is_current=True
    ).select_related('founder').prefetch_related('likes', 'views')
    
    # Create searchable text for each video
    video_matches = []
    for video in all_videos:
        searchable_text = f"{video.title} {video.founder.name if video.founder else ''}"
        try:
            founder_profile = FounderProfile.objects.get(user=video.founder)
            searchable_text += f" {founder_profile.company_name}"
        except FounderProfile.DoesNotExist:
            pass
        
        # Calculate fuzzy match score
        score = max(
            fuzz.partial_ratio(query.lower(), searchable_text.lower()),
            fuzz.token_set_ratio(query.lower(), searchable_text.lower())
        )
        
        if score > 60:  # Threshold for relevance
            video_matches.append((video, score))
    
    # Sort by score and take top 20
    video_matches.sort(key=lambda x: x[1], reverse=True)
    videos = [v[0] for v in video_matches[:20]]
    
    videos_data = []
    for video in videos:
        video_data = VideoWithFounderSerializer(video, context={'request': request}).data
        video_data['likeCount'] = video.likes.count()
        video_data['viewCount'] = video.views.count()
        if request.user.is_authenticated:
            video_data['isLiked'] = video.likes.filter(user=request.user).exists()
        else:
            video_data['isLiked'] = False
        videos_data.append(video_data)
    
    # Fuzzy search profiles
    all_users = User.objects.all()
    user_matches = []
    
    for user in all_users:
        searchable_text = user.name
        
        if user.role == 'founder':
            try:
                profile = FounderProfile.objects.get(user=user)
                searchable_text += f" {profile.company_name} {profile.sector}"
            except FounderProfile.DoesNotExist:
                pass
        elif user.role == 'investor':
            try:
                profile = InvestorProfile.objects.get(user=user)
                searchable_text += f" {profile.firm_name}"
            except InvestorProfile.DoesNotExist:
                pass
        
        score = max(
            fuzz.partial_ratio(query.lower(), searchable_text.lower()),
            fuzz.token_set_ratio(query.lower(), searchable_text.lower())
        )
        
        if score > 60:
            user_matches.append((user, score))
    
    user_matches.sort(key=lambda x: x[1], reverse=True)
    users = [u[0] for u in user_matches[:10]]
    
    profiles_data = []
    for user in users:
        profile_info = {
            'id': str(user.id),
            'name': user.name,
            'avatar_url': user.avatar_url,
            'role': user.role,
        }
        
        if user.role == 'founder':
            try:
                founder_profile = FounderProfile.objects.get(user=user)
                profile_info['company_name'] = founder_profile.company_name
                profile_info['sector'] = founder_profile.sector
                profile_info['location'] = founder_profile.location
            except FounderProfile.DoesNotExist:
                pass
        elif user.role == 'investor':
            try:
                investor_profile = InvestorProfile.objects.get(user=user)
                profile_info['firm_name'] = investor_profile.firm_name
                profile_info['title'] = investor_profile.title
            except InvestorProfile.DoesNotExist:
                pass
        
        profiles_data.append(profile_info)
    
    return Response({
        'videos': videos_data,
        'profiles': profiles_data,
        'query': query
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def autocomplete_suggestions_view(request):
    """
    Smart autocomplete with NLP-like suggestions (YouTube/TikTok style)
    Returns intelligent suggestions even if no exact matches exist
    """
    query = request.GET.get('q', '').strip().lower()
    
    if not query:
        return Response({'suggestions': []})
    
    suggestions = set()
    
    # 1. Search history from actual data (if query is 2+ chars)
    if len(query) >= 2:
        # Company names - fuzzy match
        companies = FounderProfile.objects.filter(
            company_name__isnull=False
        ).exclude(company_name='').values_list('company_name', flat=True)
        
        company_matches = process.extract(
            query, 
            companies, 
            scorer=fuzz.partial_ratio,
            limit=3
        )
        suggestions.update([match[0] for match in company_matches if match[1] > 60])
        
        # User names - fuzzy match
        users = User.objects.values_list('name', flat=True)
        user_matches = process.extract(
            query,
            users,
            scorer=fuzz.partial_ratio,
            limit=2
        )
        suggestions.update([match[0] for match in user_matches if match[1] > 60])
        
        # Sectors - fuzzy match
        sectors = FounderProfile.objects.filter(
            sector__isnull=False
        ).exclude(sector='').values_list('sector', flat=True).distinct()
        
        sector_matches = process.extract(
            query,
            sectors,
            scorer=fuzz.partial_ratio,
            limit=2
        )
        suggestions.update([match[0] for match in sector_matches if match[1] > 60])
    
    # 2. Smart English language completions (YouTube/TikTok style)
    language_suggestions = generate_smart_language_completions(query)
    suggestions.update(language_suggestions)
    
    # 3. Query expansion (if multiple words)
    query_words = query.split()
    if len(query_words) > 1:
        last_word = query_words[-1]
        prefix = ' '.join(query_words[:-1])
        
        # Get all possible completions for last word
        all_text = list(companies) if len(query) >= 2 else []
        word_completions = []
        
        for text in all_text:
            words_in_text = text.lower().split()
            for word in words_in_text:
                if word.startswith(last_word) and len(word) > len(last_word):
                    word_completions.append(f"{prefix} {word}")
        
        suggestions.update(word_completions[:2])
    
    # 4. Sort by relevance (prioritize shorter, more relevant suggestions)
    suggestions_list = list(suggestions)
    suggestions_list.sort(key=lambda x: (
        abs(len(x) - len(query)),  # Prefer similar length
        -fuzz.ratio(query, x.lower())  # Then by fuzzy score
    ))
    
    return Response({'suggestions': suggestions_list[:8]})


def generate_smart_language_completions(query):
    """
    Generate NLP-like suggestions (YouTube/TikTok style)
    Even if no data matches, suggest grammatically correct completions
    """
    completions = []
    query_lower = query.lower()
    words = query_lower.split()
    
    # Question patterns (how, what, why, etc.)
    question_patterns = {
        'how': ['how to raise', 'how to pitch', 'how to find investors', 'how to start'],
        'what': ['what is', 'what are the best', 'what investors look for', 'what makes'],
        'why': ['why investors', 'why startups', 'why founders', 'why is'],
        'when': ['when to raise', 'when to pitch', 'when should', 'when do'],
        'where': ['where to find', 'where are', 'where can', 'where do'],
        'who': ['who are the best', 'who invests in', 'who should', 'who are'],
    }
    
    # Business/startup specific completions
    business_patterns = {
        'fund': ['funding rounds', 'fundraising tips', 'funded startups', 'fund my startup'],
        'invest': ['investment opportunities', 'investors near me', 'investment thesis', 'investing in startups'],
        'pitch': ['pitch deck', 'pitching to investors', 'pitch examples', 'pitch video'],
        'seed': ['seed funding', 'seed stage', 'seed investors', 'seed round'],
        'series': ['series a', 'series b', 'series a funding', 'series funding'],
        'start': ['startup ideas', 'startups in', 'starting a company', 'startup funding'],
        'raise': ['raise capital', 'raise money', 'raising funds', 'raise seed'],
        'tech': ['tech startups', 'technology companies', 'tech investors', 'tech funding'],
        'ai': ['ai startups', 'ai companies', 'ai funding', 'artificial intelligence'],
        'saas': ['saas companies', 'saas startups', 'saas funding', 'saas business'],
        'find': ['find investors', 'find funding', 'find co-founder', 'find startup ideas'],
        'best': ['best investors', 'best startups', 'best funding', 'best pitch'],
        'top': ['top investors', 'top startups', 'top vcs', 'top founders'],
    }
    
    # Check first word for patterns
    if words:
        first_word = words[0]
        
        # Question patterns
        if first_word in question_patterns:
            for pattern in question_patterns[first_word]:
                if pattern.startswith(query_lower):
                    completions.append(pattern)
        
        # Business patterns
        if first_word in business_patterns:
            for pattern in business_patterns[first_word]:
                if pattern.startswith(query_lower):
                    completions.append(pattern)
    
    # Industry/sector completions
    sectors = ['fintech', 'healthtech', 'edtech', 'climate tech', 'ai', 'saas', 'ecommerce', 'web3']
    for sector in sectors:
        if sector.startswith(query_lower):
            completions.extend([
                f"{sector} startups",
                f"{sector} companies",
                f"{sector} investors",
            ])
    
    # Location-based suggestions
    if any(word in query_lower for word in ['in', 'near', 'at']):
        locations = ['san francisco', 'new york', 'london', 'silicon valley', 'austin', 'boston']
        for loc in locations:
            if query_lower.endswith('in ') or query_lower.endswith('near '):
                completions.append(f"{query}{loc}")
    
    # Stage-based suggestions
    stages = ['pre-seed', 'seed', 'series a', 'series b', 'growth stage']
    for stage in stages:
        if stage.startswith(query_lower):
            completions.extend([
                f"{stage} funding",
                f"{stage} startups",
                f"{stage} investors",
            ])
    
    # Amount-based suggestions
    if any(char.isdigit() for char in query_lower) or query_lower.endswith('m') or query_lower.endswith('k'):
        completions.extend([
            f"{query} funding",
            f"{query} raised",
            f"{query} valuation",
        ])
    
    return completions[:5]


@api_view(['GET'])
@permission_classes([AllowAny])
def search_suggestions_view(request):
    """
    Get popular/trending search terms
    Used for empty state / recent searches
    """
    # Get actual popular searches from your data
    popular_sectors = FounderProfile.objects.filter(
        sector__isnull=False
    ).exclude(sector='').values('sector').annotate(
        count=Count('sector')
    ).order_by('-count')[:5]
    
    suggestions = [s['sector'] for s in popular_sectors if s['sector']]
    
    # Add default popular searches
    default_suggestions = [
        'AI startups',
        'Fintech companies',
        'Seed funding',
        'Series A',
        'SaaS businesses',
        'Healthcare tech',
        'Climate tech',
        'Web3 projects'
    ]
    
    for suggestion in default_suggestions:
        if suggestion not in suggestions and len(suggestions) < 8:
            suggestions.append(suggestion)
    
    return Response({'suggestions': suggestions[:8]})