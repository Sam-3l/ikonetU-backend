from django.db.models import Q, Case, When, IntegerField, F
from .models import Video
from apps.signals.models import Signal
from apps.profiles.models import InvestorProfile


def get_smart_feed_for_investor(investor, limit=20, offset=0):
    """
    Smart feed algorithm that filters videos based on:
    1. Investor preferences (sectors, stages)
    2. Excludes already swiped founders
    3. Prioritizes by compatibility score
    """
    
    # Get investor preferences
    try:
        investor_profile = InvestorProfile.objects.get(user=investor)
        preferred_sectors = investor_profile.sectors or []
        preferred_stages = investor_profile.stages or []
    except InvestorProfile.DoesNotExist:
        preferred_sectors = []
        preferred_stages = []
    
    # Get founders already swiped (seen)
    seen_founder_ids = Signal.objects.filter(
        investor=investor
    ).values_list('founder_id', flat=True)
    
    # Base query: active current videos only
    videos = Video.objects.filter(
        status='active',
        is_current=True
    ).exclude(
        founder_id__in=seen_founder_ids  # Exclude already swiped
    ).select_related('founder').prefetch_related('likes', 'views')
    
    # Get one video per founder
    seen_founders = set()
    unique_videos = []
    for video in videos:
        if video.founder_id not in seen_founders:
            unique_videos.append(video)
            seen_founders.add(video.founder_id)
    
    # Calculate compatibility scores and sort
    scored_videos = []
    for video in unique_videos:
        score = calculate_compatibility_score(
            video,
            preferred_sectors,
            preferred_stages
        )
        scored_videos.append((video, score))
    
    # Sort by score (highest first)
    scored_videos.sort(key=lambda x: x[1], reverse=True)
    
    # Apply pagination
    paginated = scored_videos[offset:offset + limit]
    
    return [video for video, score in paginated]


def calculate_compatibility_score(video, preferred_sectors, preferred_stages):
    """
    Calculate compatibility score (0-100)
    Higher score = better match
    """
    from apps.profiles.models import FounderProfile
    
    score = 50  # Base score
    
    try:
        profile = FounderProfile.objects.get(user=video.founder)
        
        # Sector match: +30 points
        if profile.sector and profile.sector in preferred_sectors:
            score += 30
        
        # Stage match: +20 points
        if profile.stage and profile.stage in preferred_stages:
            score += 20
        
        # Location bonus: +10 if same location (future feature)
        # score += 10
        
    except FounderProfile.DoesNotExist:
        pass
    
    return score