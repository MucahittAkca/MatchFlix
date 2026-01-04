"""
Hybrid Recommendation Service
=============================
Content-Based + Collaborative Filtering hibrit öneri sistemi
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

from django.conf import settings
from django.db.models import Q, Avg, Count
from sklearn.metrics.pairwise import cosine_similarity

from apps.movies.models import Movie, Rating, Genre
from apps.recommendations.models import UserTasteProfile, MovieLensMapping, RecommendationLog


# Mood → Genre eşleştirmesi
MOOD_GENRE_MAP = {
    'happy': [35, 16, 10751, 10402],      # Comedy, Animation, Family, Music
    'emotional': [18, 10749],              # Drama, Romance
    'excited': [28, 53, 12, 80],          # Action, Thriller, Adventure, Crime
    'thoughtful': [878, 99, 9648, 36],    # Sci-Fi, Documentary, Mystery, History
    'relaxed': [35, 16, 10751],           # Comedy, Animation, Family
    'scared': [27, 53, 9648],             # Horror, Thriller, Mystery
}


class HybridRecommender:
    """
    Hibrit Öneri Sistemi
    - Content-Based: Tür, yönetmen, oyuncu benzerliği
    - Collaborative: NCF veya basit benzerlik
    - Cold Start: Popülerlik + TMDB rating
    """
    
    _instance = None
    _ncf_model = None
    _item_map = None          # MovieLens ID -> Model index
    _ml_to_movie = None       # MovieLens ID -> Our Movie ID
    _movie_to_ml = None       # Our Movie ID -> MovieLens ID
    _item_embeddings = None   # Film embedding cache
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_model()
        return cls._instance
    
    def _load_model(self):
        """NCF modelini ve mappingleri yükle"""
        try:
            model_path = getattr(settings, 'NCF_MODEL_PATH', 'ncf_model.pkl')
            mapping_path = model_path.replace('.pkl', '_ml_mapping.pkl')
            
            if os.path.exists(model_path):
                from apps.recommendations.ncf_model import NCFTrainer
                trainer = NCFTrainer.load(model_path)
                self._ncf_model = trainer.model
                self._ncf_model.eval()
                print(f"[OK] NCF modeli yuklendi: {model_path}")
                
                # Mapping'leri yükle
                if os.path.exists(mapping_path):
                    with open(mapping_path, 'rb') as f:
                        ml_data = pickle.load(f)
                        self._item_map = ml_data.get('item_map', {})
                        self._ml_to_movie = ml_data.get('ml_to_movie', {})
                        # Reverse mapping
                        self._movie_to_ml = {v: k for k, v in self._ml_to_movie.items()}
                    print(f"[OK] Mappings yuklendi: {len(self._item_map)} film")
                
                # Film embedding'lerini önceden hesapla
                self._precompute_embeddings()
            else:
                print("[INFO] NCF modeli bulunamadi, sadece Content-Based kullanilacak")
                self._ncf_model = None
        except Exception as e:
            print(f"[WARN] NCF model yukleme hatasi: {e}")
            self._ncf_model = None
    
    def _precompute_embeddings(self):
        """Film embedding'lerini önceden hesapla (performans için)"""
        if self._ncf_model is None or not self._item_map:
            return
        
        import torch
        self._item_embeddings = {}
        
        for ml_id, idx in self._item_map.items():
            if ml_id in self._ml_to_movie:
                movie_id = self._ml_to_movie[ml_id]
                emb = self._ncf_model.get_item_embedding(idx)
                self._item_embeddings[movie_id] = emb
        
        print(f"[OK] {len(self._item_embeddings)} film embedding'i hesaplandi")
    
    def get_or_create_profile(self, user) -> UserTasteProfile:
        """Kullanıcı profili al veya oluştur"""
        profile, created = UserTasteProfile.objects.get_or_create(user=user)
        if created or not profile.genre_weights:
            profile.update_from_ratings()
        return profile
    
    def get_content_score(self, profile: UserTasteProfile, movie: Movie) -> float:
        """
        Content-Based skor (0-1)
        - Tür benzerliği
        - Favori yönetmen/oyuncu bonusu
        """
        if not profile or not profile.genre_weights:
            return 0.5
        
        score = 0.0
        weights_sum = sum(profile.genre_weights.values())
        
        if weights_sum == 0:
            return 0.5
        
        # Tür benzerliği (weighted average)
        movie_genre_ids = list(movie.genres.values_list('id', flat=True))
        for genre_id in movie_genre_ids:
            weight = profile.genre_weights.get(str(genre_id), 0)
            score += weight
        
        if movie_genre_ids:
            score = score / len(movie_genre_ids)
        
        # Favori yönetmen bonusu (+0.15)
        if profile.favorite_directors:
            director_ids = list(movie.crew.filter(job='Director').values_list('person_id', flat=True))
            for d_id in director_ids:
                if d_id in profile.favorite_directors:
                    score += 0.15
                    break
        
        # Favori oyuncu bonusu (+0.1 per actor, max 0.2)
        if profile.favorite_actors:
            actor_ids = list(movie.cast.all()[:5].values_list('person_id', flat=True))
            actor_bonus = 0
            for a_id in actor_ids:
                if a_id in profile.favorite_actors:
                    actor_bonus += 0.1
            score += min(actor_bonus, 0.2)
        
        return min(max(score, 0.0), 1.0)
    
    def get_collaborative_score(self, user, movie: Movie) -> float:
        """
        Collaborative Filtering skor (0-1)
        NCF embedding benzerliği kullan (varsa)
        """
        # NCF embedding-based similarity
        if self._item_embeddings and movie.id in self._item_embeddings:
            try:
                # Kullanıcının beğendiği filmler
                user_ratings = Rating.objects.filter(user=user, score__gte=7)
                if user_ratings.exists():
                    liked_ids = list(user_ratings.values_list('movie_id', flat=True))
                    
                    # Beğenilen filmlerin embedding'leri
                    liked_embeddings = []
                    for lid in liked_ids[:20]:  # Max 20 film
                        if lid in self._item_embeddings:
                            liked_embeddings.append(self._item_embeddings[lid])
                    
                    if liked_embeddings:
                        # Ortalama beğeni vektörü
                        avg_liked = np.mean(liked_embeddings, axis=0)
                        movie_emb = self._item_embeddings[movie.id]
                        
                        # Cosine similarity
                        sim = cosine_similarity([avg_liked], [movie_emb])[0][0]
                        return float((sim + 1) / 2)  # [-1,1] -> [0,1]
            except Exception:
                pass
        
        # Fallback: Basit item-based CF (tür benzerliği)
        user_ratings = Rating.objects.filter(user=user, score__gte=7)
        if not user_ratings.exists():
            return 0.5
        
        liked_movie_ids = list(user_ratings.values_list('movie_id', flat=True))
        liked_genres = set()
        for m in Movie.objects.filter(id__in=liked_movie_ids).prefetch_related('genres'):
            liked_genres.update(m.genres.values_list('id', flat=True))
        
        movie_genres = set(movie.genres.values_list('id', flat=True))
        
        if not liked_genres:
            return 0.5
        
        # Jaccard similarity
        intersection = len(liked_genres & movie_genres)
        union = len(liked_genres | movie_genres)
        
        return intersection / union if union > 0 else 0.5
    
    def get_popularity_score(self, movie: Movie) -> float:
        """Popülerlik skoru (0-1)"""
        # TMDB vote average (0-10) → (0-1)
        vote_score = (movie.vote_average or 0) / 10.0
        
        # Vote count bonus (log scale)
        if movie.vote_count:
            count_bonus = min(np.log10(movie.vote_count + 1) / 5, 0.2)
        else:
            count_bonus = 0
        
        return min(vote_score + count_bonus, 1.0)
    
    def recommend(
        self,
        user,
        n: int = 10,
        mood: str = None,
        time_available: str = None,
        era: str = None,
        genre_id: int = None,
        exclude_watched: bool = True,
        exclude_watchlist: bool = False
    ) -> List[Dict]:
        """
        Hibrit öneri al
        
        Args:
            user: Kullanıcı
            n: Öneri sayısı
            mood: Ruh hali (happy, emotional, excited, thoughtful, relaxed, scared)
            time_available: Süre (short: <90dk, medium: 90-120dk, long: >120dk)
            era: Dönem (recent: 2020+, 2010s, 2000s, classic: <2000)
            genre_id: Belirli tür filtresi
            exclude_watched: İzlenenleri hariç tut
            exclude_watchlist: Watchlist'tekileri hariç tut
        
        Returns:
            List of dicts with movie and scores
        """
        
        # Kullanıcı profili
        profile = self.get_or_create_profile(user)
        
        # Ağırlıklar (cold start'a göre ayarla)
        if profile.total_rated_movies < 3:
            # Cold start - popülerliğe ağırlık ver
            content_w, collab_w, pop_w = 0.2, 0.0, 0.8
        elif profile.total_rated_movies < 10:
            content_w, collab_w, pop_w = 0.4, 0.2, 0.4
        elif profile.total_rated_movies < 30:
            content_w, collab_w, pop_w = 0.5, 0.3, 0.2
        else:
            # Yeterli veri var
            content_w, collab_w, pop_w = 0.4, 0.5, 0.1
        
        # Base queryset
        candidates = Movie.objects.filter(
            poster_path__isnull=False
        ).exclude(poster_path='')
        
        # İzlenenleri hariç tut (Rating + WatchedMovie)
        if exclude_watched:
            from apps.movies.models import Watchlist, WatchedMovie
            # Puanlanan filmler
            rated_ids = set(Rating.objects.filter(user=user).values_list('movie_id', flat=True))
            # İzlendi olarak işaretlenen filmler
            watched_ids = set(WatchedMovie.objects.filter(user=user).values_list('movie_id', flat=True))
            # Birleştir ve hariç tut
            all_watched_ids = rated_ids | watched_ids
            candidates = candidates.exclude(id__in=all_watched_ids)
        
        # Watchlist'tekileri hariç tut
        if exclude_watchlist:
            from apps.movies.models import Watchlist
            watchlist_ids = Watchlist.objects.filter(user=user).values_list('movie_id', flat=True)
            candidates = candidates.exclude(id__in=watchlist_ids)
        
        # Mood filtresi
        if mood and mood in MOOD_GENRE_MAP:
            mood_genre_tmdb_ids = MOOD_GENRE_MAP[mood]
            candidates = candidates.filter(genres__tmdb_id__in=mood_genre_tmdb_ids)
        
        # Süre filtresi
        if time_available == 'short':
            candidates = candidates.filter(runtime__lt=90)
        elif time_available == 'medium':
            candidates = candidates.filter(runtime__gte=90, runtime__lte=120)
        elif time_available == 'long':
            candidates = candidates.filter(runtime__gt=120)
        
        # Dönem filtresi
        if era == 'recent':
            candidates = candidates.filter(release_date__year__gte=2020)
        elif era == '2010s':
            candidates = candidates.filter(release_date__year__gte=2010, release_date__year__lt=2020)
        elif era == '2000s':
            candidates = candidates.filter(release_date__year__gte=2000, release_date__year__lt=2010)
        elif era == 'classic':
            candidates = candidates.filter(release_date__year__lt=2000)
        
        # Tür filtresi
        if genre_id:
            candidates = candidates.filter(genres__id=genre_id)
        
        # Performans için limit
        candidates = candidates.distinct().prefetch_related('genres', 'cast', 'crew')[:300]
        
        # Skorları hesapla
        scored_movies = []
        for movie in candidates:
            content_score = self.get_content_score(profile, movie)
            collab_score = self.get_collaborative_score(user, movie)
            pop_score = self.get_popularity_score(movie)
            
            final_score = (
                content_w * content_score +
                collab_w * collab_score +
                pop_w * pop_score
            )
            
            scored_movies.append({
                'movie': movie,
                'final_score': final_score,
                'content_score': content_score,
                'collab_score': collab_score,
                'pop_score': pop_score,
            })
        
        # Sırala ve döndür
        scored_movies.sort(key=lambda x: x['final_score'], reverse=True)
        
        return scored_movies[:n]
    
    def get_similar_movies(self, movie: Movie, n: int = 10) -> List[Movie]:
        """Bir filme benzer filmler"""
        
        movie_genres = set(movie.genres.values_list('id', flat=True))
        movie_directors = set(movie.crew.filter(job='Director').values_list('person_id', flat=True))
        movie_actors = set(movie.cast.all()[:5].values_list('person_id', flat=True))
        
        candidates = Movie.objects.exclude(id=movie.id).filter(
            poster_path__isnull=False
        ).prefetch_related('genres', 'cast', 'crew')[:200]
        
        scored = []
        for candidate in candidates:
            score = 0.0
            
            # Tür benzerliği (0.5 weight)
            cand_genres = set(candidate.genres.values_list('id', flat=True))
            if movie_genres and cand_genres:
                genre_sim = len(movie_genres & cand_genres) / len(movie_genres | cand_genres)
                score += 0.5 * genre_sim
            
            # Yönetmen benzerliği (0.3 weight)
            cand_directors = set(candidate.crew.filter(job='Director').values_list('person_id', flat=True))
            if movie_directors & cand_directors:
                score += 0.3
            
            # Oyuncu benzerliği (0.2 weight)
            cand_actors = set(candidate.cast.all()[:5].values_list('person_id', flat=True))
            if movie_actors and cand_actors:
                actor_overlap = len(movie_actors & cand_actors) / 5
                score += 0.2 * actor_overlap
            
            scored.append((candidate, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [m for m, _ in scored[:n]]
    
    def calculate_compatibility(self, user_a, user_b) -> Dict:
        """İki kullanıcı arasında uyumluluk skoru"""
        
        profile_a = self.get_or_create_profile(user_a)
        profile_b = self.get_or_create_profile(user_b)
        
        # 1. Tür benzerliği
        all_genres = set(profile_a.genre_weights.keys()) | set(profile_b.genre_weights.keys())
        if all_genres:
            vec_a = [profile_a.genre_weights.get(g, 0) for g in all_genres]
            vec_b = [profile_b.genre_weights.get(g, 0) for g in all_genres]
            
            if sum(vec_a) > 0 and sum(vec_b) > 0:
                genre_sim = cosine_similarity([vec_a], [vec_b])[0][0]
            else:
                genre_sim = 0.5
        else:
            genre_sim = 0.5
        
        # 2. Ortak izlenen filmler (WatchedMovie tablosundan)
        from apps.movies.models import WatchedMovie
        watched_a = set(WatchedMovie.objects.filter(user=user_a).values_list('movie_id', flat=True))
        watched_b = set(WatchedMovie.objects.filter(user=user_b).values_list('movie_id', flat=True))
        common_movies = watched_a & watched_b
        
        if common_movies:
            # Puan benzerliği (MAE tabanlı)
            diffs = []
            for movie_id in list(common_movies)[:50]:  # Performans limiti
                try:
                    r_a = Rating.objects.get(user=user_a, movie_id=movie_id).score
                    r_b = Rating.objects.get(user=user_b, movie_id=movie_id).score
                    diffs.append(abs(r_a - r_b))
                except Rating.DoesNotExist:
                    continue
            
            if diffs:
                rating_sim = 1 - (sum(diffs) / len(diffs) / 10)
            else:
                rating_sim = 0.5
        else:
            rating_sim = 0.5
        
        # 3. Favori kişi benzerliği
        common_actors = set(profile_a.favorite_actors or []) & set(profile_b.favorite_actors or [])
        common_directors = set(profile_a.favorite_directors or []) & set(profile_b.favorite_directors or [])
        person_sim = min((len(common_actors) + len(common_directors) * 2) / 10, 1.0)
        
        # Final skor
        final_score = (genre_sim * 0.4) + (rating_sim * 0.4) + (person_sim * 0.2)
        
        return {
            'score': int(final_score * 100),
            'common_movies': len(common_movies),
            'genre_similarity': int(genre_sim * 100),
            'rating_similarity': int(rating_sim * 100),
            'common_actors': len(common_actors),
            'common_directors': len(common_directors),
        }
    
    def get_movies_for_both(self, user_a, user_b, n: int = 10) -> List[Dict]:
        """İki kullanıcı için ortak film önerileri (birlikte izlemek için)"""
        from apps.movies.models import WatchedMovie
        
        # Her iki kullanıcının da izlemediği filmler (Rating + WatchedMovie)
        rated_a = set(Rating.objects.filter(user=user_a).values_list('movie_id', flat=True))
        rated_b = set(Rating.objects.filter(user=user_b).values_list('movie_id', flat=True))
        watched_a = set(WatchedMovie.objects.filter(user=user_a).values_list('movie_id', flat=True))
        watched_b = set(WatchedMovie.objects.filter(user=user_b).values_list('movie_id', flat=True))
        
        all_watched = rated_a | rated_b | watched_a | watched_b
        
        profile_a = self.get_or_create_profile(user_a)
        profile_b = self.get_or_create_profile(user_b)
        
        candidates = Movie.objects.exclude(id__in=all_watched).filter(
            poster_path__isnull=False
        ).prefetch_related('genres', 'cast', 'crew')[:200]
        
        scored = []
        for movie in candidates:
            score_a = self.get_content_score(profile_a, movie)
            score_b = self.get_content_score(profile_b, movie)
            
            # Minimum skoru al (her ikisinin de sevmesi gerekiyor)
            combined = min(score_a, score_b)
            
            # Popülerlik bonusu
            pop_bonus = self.get_popularity_score(movie) * 0.2
            combined += pop_bonus
            
            # Skorları yüzdelik olarak kaydet (0-100)
            scored.append({
                'movie': movie,
                'combined_score': min(combined * 100, 100),
                'score_a': min(score_a * 100, 100),
                'score_b': min(score_b * 100, 100),
            })
        
        scored.sort(key=lambda x: x['combined_score'], reverse=True)
        return scored[:n]


# Singleton instance
recommender = HybridRecommender()

