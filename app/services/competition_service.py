from app.models.competition import Competition, CompetitionStatus, CompetitionRound
from app import db
import random
from typing import List, Tuple, Dict
from datetime import datetime

class CompetitionService:
    @staticmethod
    def create_competition(name: str, date: datetime, dance_level: str, organizer_id: int) -> Competition:
        """Create a new competition"""
        competition = Competition(
            name=name,
            date=date,
            dance_level=dance_level,
            organizer_id=organizer_id,
            status=CompetitionStatus.DRAFT
        )
        db.session.add(competition)
        db.session.commit()
        return competition

    @staticmethod
    def open_registration(competition_id: int) -> Competition:
        """Open registration for a competition"""
        competition = Competition.query.get(competition_id)
        if competition.status == CompetitionStatus.DRAFT:
            competition.status = CompetitionStatus.REGISTRATION_OPEN
            db.session.commit()
        return competition

    @staticmethod
    def close_registration(competition_id: int) -> Competition:
        """Close registration for a competition"""
        competition = Competition.query.get(competition_id)
        if competition.status == CompetitionStatus.REGISTRATION_OPEN:
            competition.status = CompetitionStatus.REGISTRATION_CLOSED
            db.session.commit()
        return competition

    @staticmethod
    def register_participant(competition_id: int, user_id: int, role: str) -> bool:
        """Register a participant for the competition"""
        competition = Competition.query.get(competition_id)
        if competition.status != CompetitionStatus.REGISTRATION_OPEN:
            return False

        if role.upper() == 'LEADER':
            competition.leaders.append(user_id)
        elif role.upper() == 'FOLLOWER':
            competition.followers.append(user_id)
        else:
            return False

        db.session.commit()
        return True

    @staticmethod
    def assign_judges(competition_id: int, judge_ids: List[int]) -> bool:
        """Assign judges to the competition"""
        competition = Competition.query.get(competition_id)
        if competition.status not in [CompetitionStatus.DRAFT, CompetitionStatus.REGISTRATION_OPEN]:
            return False

        competition.judges = judge_ids
        db.session.commit()
        return True

    @staticmethod
    def start_competition(competition_id: int) -> Tuple[bool, str]:
        """Start the competition if all requirements are met"""
        competition = Competition.query.get(competition_id)
        
        if not competition.can_start():
            return False, "Competition requirements not met"

        competition.status = CompetitionStatus.IN_PROGRESS
        competition.current_round = CompetitionRound.PRELIMINARY
        db.session.commit()
        return True, "Competition started successfully"

    @staticmethod
    def generate_random_couples(competition_id: int) -> List[Tuple[int, int]]:
        """Generate random couples for the current round"""
        competition = Competition.query.get(competition_id)
        leaders = list(competition.leaders)
        followers = list(competition.followers)
        
        # Shuffle both lists
        random.shuffle(leaders)
        random.shuffle(followers)
        
        # Match leaders and followers
        couples = []
        max_pairs = min(len(leaders), len(followers))
        
        for i in range(max_pairs):
            couples.append((leaders[i], followers[i]))
        
        return couples

    @staticmethod
    def advance_round(competition_id: int, advancing_couples: List[Tuple[int, int]]) -> bool:
        """Advance the competition to the next round"""
        competition = Competition.query.get(competition_id)
        
        round_order = [
            CompetitionRound.PRELIMINARY,
            CompetitionRound.QUARTER_FINAL,
            CompetitionRound.SEMI_FINAL,
            CompetitionRound.FINAL
        ]
        
        current_index = round_order.index(competition.current_round)
        if current_index + 1 >= len(round_order):
            competition.status = CompetitionStatus.COMPLETED
        else:
            competition.current_round = round_order[current_index + 1]
        
        db.session.commit()
        return True

    @staticmethod
    def calculate_points(competition_id: int, final_rankings: List[Dict]) -> Dict:
        """Calculate points based on competition tier and rankings"""
        competition = Competition.query.get(competition_id)
        
        # Points by tier and placement
        tier_points = {
            1: {1: 5, 2: 4, 3: 3, 4: 2, 5: 1},
            2: {1: 10, 2: 8, 3: 6, 4: 4, 5: 2},
            3: {1: 15, 2: 12, 3: 10, 4: 8, 5: 6}
        }
        
        results = {}
        for ranking in final_rankings:
            placement = ranking['placement']
            leader_id = ranking['leader_id']
            follower_id = ranking['follower_id']
            
            # Calculate points based on tiers
            leader_points = tier_points[competition.leader_tier.value].get(placement, 0)
            follower_points = tier_points[competition.follower_tier.value].get(placement, 0)
            
            results[leader_id] = leader_points
            results[follower_id] = follower_points
        
        return results
