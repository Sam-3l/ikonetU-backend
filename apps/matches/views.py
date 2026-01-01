from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count, Max, Prefetch
from .models import Match, Message
from apps.accounts.models import User
from apps.profiles.models import FounderProfile, InvestorProfile


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_matches_view(request):
    """Get all matches for current user"""
    user = request.user
    
    # Get matches based on role
    if user.role == 'investor':
        matches = Match.objects.filter(investor=user)
    elif user.role == 'founder':
        matches = Match.objects.filter(founder=user)
    else:
        return Response({'message': 'Invalid role'}, status=status.HTTP_403_FORBIDDEN)
    
    # Annotate with message counts and last message
    matches = (
        matches
        .annotate(
            message_count=Count('messages'),
            last_message_time=Max('messages__created_at')
        )
        .select_related('investor', 'founder')
        .prefetch_related(
            Prefetch(
                'messages',
                queryset=Message.objects.order_by('-created_at'),
                to_attr='ordered_messages'
            )
        )
        .order_by('-last_message_time', '-created_at')
    )
    
    # Serialize matches
    data = []
    for match in matches:
        # Determine the "other user" based on current user's role
        if user.role == 'investor':
            other_user = match.founder
            try:
                other_profile = FounderProfile.objects.get(user=other_user)
                profile_data = {
                    'company_name': other_profile.company_name,
                    'sector': other_profile.sector,
                    'stage': other_profile.stage,
                    'location': other_profile.location,
                }
            except FounderProfile.DoesNotExist:
                profile_data = None
        else:
            other_user = match.investor
            try:
                other_profile = InvestorProfile.objects.get(user=other_user)
                profile_data = {
                    'firm_name': other_profile.firm_name,
                    'title': other_profile.title,
                    'sectors': other_profile.sectors,
                    'stages': other_profile.stages,
                }
            except InvestorProfile.DoesNotExist:
                profile_data = None
        
        # Get last message
        last_message = match.ordered_messages[0] if match.ordered_messages else None
        
        # Count unread messages (status is 'sent' or 'delivered', not 'read')
        unread_count = Message.objects.filter(
            match=match,
            status__in=['sent', 'delivered']
        ).exclude(sender=user).count()
        
        data.append({
            'id': str(match.id),
            'is_active': match.is_active,
            'created_at': match.created_at.isoformat(),
            'other_user': {
                'id': str(other_user.id),
                'name': other_user.name,
                'avatar_url': other_user.avatar_url,
                'role': other_user.role,
            },
            'other_profile': profile_data,
            'last_message': {
                'id': str(last_message.id),
                'content': last_message.content,
                'sender_id': str(last_message.sender_id),
                'status': last_message.status,
                'created_at': last_message.created_at.isoformat(),
            } if last_message else None,
            'unread_count': unread_count,
        })
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def match_detail_view(request, match_id):
    """Get specific match details"""
    user = request.user
    
    try:
        # Ensure user is part of this match
        match = Match.objects.get(
            Q(id=match_id) & (Q(investor=user) | Q(founder=user))
        )
    except Match.DoesNotExist:
        return Response({'message': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Determine other user
    other_user = match.founder if user.role == 'investor' else match.investor
    
    # Get profile
    if other_user.role == 'founder':
        try:
            profile = FounderProfile.objects.get(user=other_user)
            profile_data = {
                'company_name': profile.company_name,
                'sector': profile.sector,
                'stage': profile.stage,
                'location': profile.location,
                'bio': profile.bio,
            }
        except FounderProfile.DoesNotExist:
            profile_data = None
    else:
        try:
            profile = InvestorProfile.objects.get(user=other_user)
            profile_data = {
                'firm_name': profile.firm_name,
                'title': profile.title,
                'thesis': profile.thesis,
                'sectors': profile.sectors,
                'stages': profile.stages,
            }
        except InvestorProfile.DoesNotExist:
            profile_data = None
    
    return Response({
        'id': str(match.id),
        'is_active': match.is_active,
        'created_at': match.created_at.isoformat(),
        'other_user': {
            'id': str(other_user.id),
            'name': other_user.name,
            'avatar_url': other_user.avatar_url,
            'role': other_user.role,
        },
        'other_profile': profile_data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unmatch_view(request, match_id):
    """Unmatch (deactivate match)"""
    user = request.user
    
    try:
        match = Match.objects.get(
            Q(id=match_id) & (Q(investor=user) | Q(founder=user))
        )
    except Match.DoesNotExist:
        return Response({'message': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)
    
    match.is_active = False
    match.save()
    
    return Response({'message': 'Unmatched successfully'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_match_view(request, match_id):
    """Accept a pending match (investor only)"""
    user = request.user
    
    if user.role != 'investor':
        return Response(
            {'message': 'Only investors can accept matches'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        match = Match.objects.get(id=match_id, investor=user, is_active=False)
    except Match.DoesNotExist:
        return Response(
            {'message': 'Match not found or already active'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    match.is_active = True
    match.save()
    
    return Response({
        'message': 'Match accepted',
        'match': {
            'id': str(match.id),
            'is_active': match.is_active
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_match_view(request, match_id):
    """Reject a pending match (investor only)"""
    user = request.user
    
    if user.role != 'investor':
        return Response(
            {'message': 'Only investors can reject matches'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        match = Match.objects.get(id=match_id, investor=user, is_active=False)
    except Match.DoesNotExist:
        return Response(
            {'message': 'Match not found or already processed'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    match.delete()  # Permanently delete rejected matches
    
    return Response({'message': 'Match rejected'})