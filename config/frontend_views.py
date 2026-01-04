from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, authenticate, login as auth_login, logout as auth_logout
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.http import JsonResponse
from django.db.models import Q, Avg
from django.db import connection
from apps.movies.models import Movie, Genre, Rating, Watchlist, WatchedMovie, Person, MovieCast, MovieCrew
from apps.users.models import Friendship
from apps.movies.services import TMDBService
import json

User = get_user_model()


def health_check(request):
    """Health check endpoint for Docker and Azure"""
    try:
        # Check database connection
        connection.ensure_connection()
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)


def register(request):
    """Kayıt sayfası"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        if password != password2:
            return render(request, 'register.html', {'error': 'Şifreler eşleşmiyor'})
        
        if len(password) < 8:
            return render(request, 'register.html', {'error': 'Şifre en az 8 karakter olmalıdır'})
        
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Kullanıcı adı zaten kullanılıyor'})
        
        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error': 'Bu e-posta adresi zaten kullanılıyor'})
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        auth_login(request, user)
        return redirect('onboarding')  # Yeni kullanıcıları onboarding'e yönlendir
    
    return render(request, 'register.html')


def login(request):
    """Giriş sayfası"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Kullanıcı adı veya şifre yanlış'})
    
    return render(request, 'login.html')


def logout(request):
    """Çıkış"""
    auth_logout(request)
    return redirect('landing')


def landing(request):
    """Landing page"""
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'landing.html')


@login_required
def home(request):
    """Home page - AI destekli kişiselleştirilmiş öneriler"""
    from django.db.models import Avg
    from datetime import date, timedelta
    from apps.recommendations.services import HybridRecommender
    
    # Onboarding kontrolü - tamamlanmadıysa yönlendir
    if not request.user.onboarding_completed:
        return redirect('onboarding')
    
    # AI Öneri Sistemi
    recommender = HybridRecommender()
    
    # Kişiselleştirilmiş öneriler
    ai_recommendations = recommender.recommend(
        user=request.user,
        n=10,
        exclude_watched=True
    )
    recommended_movies = [r['movie'] for r in ai_recommendations]
    
    # Trending (popülerlik + yüksek puan)
    trending_movies = Movie.objects.filter(
        vote_average__gte=7.0
    ).order_by('-popularity')[:10]
    
    # Vizyona girecek filmler
    today = date.today()
    next_month = today + timedelta(days=30)
    upcoming_movies = Movie.objects.filter(
        release_date__gte=today,
        release_date__lte=next_month
    ).order_by('release_date')[:10]
    
    # Türler
    genres = Genre.objects.all()[:6]
    
    # Kullanıcının ortalama puanı
    avg_rating = request.user.ratings.aggregate(Avg('score'))['score__avg'] or 0
    
    # Kullanıcı profil özeti
    try:
        profile = request.user.taste_profile
        top_genres = sorted(
            profile.genre_weights.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3] if profile.genre_weights else []
    except:
        profile = None
        top_genres = []
    
    context = {
        'recommended_movies': recommended_movies,
        'trending_movies': trending_movies,
        'upcoming_movies': upcoming_movies,
        'genres': genres,
        'avg_rating': round(avg_rating, 1),
        'profile': profile,
        'is_ai_powered': len(ai_recommendations) > 0,
    }
    
    return render(request, 'home.html', context)


def movie_detail(request, movie_id):
    """Film detayı sayfası"""
    movie = get_object_or_404(Movie, id=movie_id)
    
    # Benzer filmler
    similar_movies = Movie.objects.filter(
        genres__id__in=movie.genres.values_list('id', flat=True)
    ).exclude(id=movie.id).distinct().order_by('-vote_average')[:6]
    
    # Puanlamalar
    ratings = movie.ratings.select_related('user').order_by('-created_at')[:5]
    
    # Kullanıcı puanı ve izleme durumu (varsa)
    user_rating = None
    is_in_watchlist = False
    watched_movie = None
    if request.user.is_authenticated:
        user_rating = movie.ratings.filter(user=request.user).first()
        is_in_watchlist = Watchlist.objects.filter(user=request.user, movie=movie).exists()
        watched_movie = WatchedMovie.objects.filter(user=request.user, movie=movie).first()
    
    # İzleme platformları (JustWatch verisi)
    watch_providers = {}
    if movie.tmdb_id:
        try:
            tmdb = TMDBService()
            watch_providers = tmdb.get_watch_providers(movie.tmdb_id)
        except Exception:
            pass
    
    context = {
        'movie': movie,
        'similar_movies': similar_movies,
        'ratings': ratings,
        'user_rating': user_rating,
        'is_in_watchlist': is_in_watchlist,
        'watched_movie': watched_movie,
        'rating_range': range(1, 11),  # 1-10 arası puan seçenekleri
        'watch_providers': watch_providers,
    }
    
    return render(request, 'movie_detail.html', context)


@login_required
def quick_match(request):
    """Hızlı Öneri - Tek başına veya arkadaşla film önerisi"""
    from apps.recommendations.services import HybridRecommender
    from apps.users.models import User
    from apps.movies.models import Genre
    
    # Kullanıcının arkadaşları ve türler
    friends = request.user.get_friends()
    genres = Genre.objects.all().order_by('name_tr')
    
    # POST: Sonuçları hesapla
    if request.method == 'POST':
        mode = request.POST.get('mode', 'solo')  # 'solo' veya 'friend'
        friend_id = request.POST.get('friend_id', '')
        mood = request.POST.get('mood', '')
        time_available = request.POST.get('time_available', '')
        era = request.POST.get('era', '')
        genre_id = request.POST.get('genre_id', '')
        
        recommender = HybridRecommender()
        
        # SOLO MODE
        if mode == 'solo' or not friend_id:
            # Kişiye özel öneri (tarz dışı istekler için filtreler kullan)
            recommendations = recommender.recommend(
                user=request.user,
                n=12,
                mood=mood if mood else None,
                time_available=time_available if time_available else None,
                era=era if era else None,
                genre_id=int(genre_id) if genre_id else None,
                exclude_watched=True
            )
            
            context = {
                'friends': friends,
                'genres': genres,
                'mode': 'solo',
                'recommendations': recommendations,
                'mood': mood,
                'time_available': time_available,
                'era': era,
                'genre_id': genre_id,
                'show_results': True,
            }
        
        # FRIEND MODE
        else:
            try:
                friend = User.objects.get(id=friend_id)
                
                # Uyumluluk hesapla
                compatibility = recommender.calculate_compatibility(request.user, friend)
                
                # İkisi için ortak film önerileri
                joint_recommendations = recommender.get_movies_for_both(
                    request.user, 
                    friend, 
                    n=12
                )
                
                # Ek filtreleri uygula
                if mood or time_available or era:
                    filtered_recs = []
                    for rec in joint_recommendations:
                        movie = rec['movie']
                        # Süre filtresi
                        if time_available == 'short' and movie.runtime and movie.runtime >= 90:
                            continue
                        if time_available == 'medium' and movie.runtime and (movie.runtime < 90 or movie.runtime > 120):
                            continue
                        if time_available == 'long' and movie.runtime and movie.runtime <= 120:
                            continue
                        # Era filtresi
                        if era and movie.release_date:
                            year = movie.release_date.year
                            if era == 'recent' and year < 2020:
                                continue
                            if era == '2010s' and (year < 2010 or year >= 2020):
                                continue
                            if era == '2000s' and (year < 2000 or year >= 2010):
                                continue
                            if era == 'classic' and year >= 2000:
                                continue
                        filtered_recs.append(rec)
                    joint_recommendations = filtered_recs[:12]
                
                context = {
                    'friends': friends,
                    'genres': genres,
                    'mode': 'friend',
                    'selected_friend': friend,
                    'compatibility': compatibility,
                    'recommendations': joint_recommendations,
                    'mood': mood,
                    'time_available': time_available,
                    'era': era,
                    'show_results': True,
                }
                
            except User.DoesNotExist:
                context = {
                    'friends': friends,
                    'genres': genres,
                    'error': 'Arkadaş bulunamadı.',
                    'show_results': False,
                }
        
        return render(request, 'quick_match.html', context)
    
    # GET: Form göster
    context = {
        'friends': friends,
        'genres': genres,
        'show_results': False,
    }
    
    return render(request, 'quick_match.html', context)


@login_required
def watchlist(request):
    """İzleme listesi sayfası"""
    watchlist_items = Watchlist.objects.filter(user=request.user).select_related('movie').order_by('-added_at')
    
    context = {
        'watchlist_items': watchlist_items,
    }
    
    return render(request, 'watchlist.html', context)


@login_required
def explore(request):
    """Keşfet sayfası - Önce kütüphane, sonra TMDB asenkron"""
    from django.core.paginator import Paginator
    
    search_query = request.GET.get('search', '').strip()
    genre = request.GET.get('genre', '')
    rating_gte = request.GET.get('rating_gte', '')
    year = request.GET.get('year', '')
    ordering = request.GET.get('ordering', '-popularity')
    page = int(request.GET.get('page', 1))
    
    # Kütüphaneden ara (fuzzy search)
    movies = Movie.objects.all()
    
    if search_query:
        # Fuzzy arama: kelimeleri ayır ve her biri için OR sorgusu yap
        words = search_query.split()
        query = Q()
        for word in words:
            if len(word) >= 2:
                query |= Q(title__icontains=word)
                query |= Q(original_title__icontains=word)
        
        if query:
            movies = movies.filter(query).distinct()
    
    # Filtreleme
    if genre:
        movies = movies.filter(genres__id=genre)
    
    if rating_gte:
        try:
            movies = movies.filter(vote_average__gte=float(rating_gte))
        except ValueError:
            pass
    
    if year:
        try:
            movies = movies.filter(release_date__year=int(year))
        except ValueError:
            pass
    
    # Sıralama
    movies = movies.order_by(ordering)
    
    # Sayfalama
    paginator = Paginator(movies, 20)
    movies = paginator.get_page(page)
    
    genres = Genre.objects.all()
    
    # TMDB'den de aranacak mı?
    should_search_tmdb = bool(search_query and len(search_query) >= 2) or bool(genre or rating_gte or year)
    
    context = {
        'movies': movies,
        'genres': genres,
        'paginator': paginator,
        'should_search_tmdb': should_search_tmdb,
        'current_filters': {
            'search': search_query,
            'genre': genre,
            'rating_gte': rating_gte,
            'year': year,
            'ordering': ordering,
        }
    }
    
    return render(request, 'explore.html', context)


@login_required
@require_GET
def live_search(request):
    """Yazarken ara - önce kütüphane, sonra TMDB"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'success': True, 'local': [], 'tmdb': []})
    
    # 1. Kütüphaneden ara (fuzzy)
    words = query.split()
    db_query = Q()
    for word in words:
        if len(word) >= 2:
            db_query |= Q(title__icontains=word)
            db_query |= Q(original_title__icontains=word)
    
    local_movies = []
    if db_query:
        movies = Movie.objects.filter(db_query).distinct().order_by('-popularity')[:10]
        for movie in movies:
            local_movies.append({
                'id': movie.id,
                'title': movie.title,
                'poster_url': movie.poster_url,
                'vote_average': movie.vote_average,
                'year': movie.year,
                'source': 'local'
            })
    
    return JsonResponse({
        'success': True,
        'local': local_movies,
    })


@login_required
@require_GET
def live_search_tmdb(request):
    """Yazarken ara - TMDB kısmı (ayrı endpoint, daha yavaş)"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'success': True, 'tmdb': []})
    
    tmdb_movies = []
    local_ids = set(Movie.objects.filter(
        Q(title__icontains=query) | Q(original_title__icontains=query)
    ).values_list('tmdb_id', flat=True))
    
    try:
        tmdb = TMDBService()
        results = tmdb.search_movie(query, page=1)
        
        for movie_data in results.get('results', [])[:10]:
            # Kütüphanede yoksa göster
            if movie_data['id'] not in local_ids:
                # Import et
                movie = import_movie_to_db(movie_data)
                if movie:
                    tmdb_movies.append({
                        'id': movie.id,
                        'title': movie.title,
                        'poster_url': movie.poster_url,
                        'vote_average': movie.vote_average,
                        'year': movie.year,
                        'source': 'tmdb'
                    })
    except Exception as e:
        print(f"TMDB live search error: {e}")
    
    return JsonResponse({
        'success': True,
        'tmdb': tmdb_movies,
    })


@login_required
@require_GET
def tmdb_async_search(request):
    """TMDB'den asenkron arama - sonuçları kütüphaneye ekle ve döndür"""
    search_query = request.GET.get('search', '').strip()
    genre = request.GET.get('genre', '')
    rating_gte = request.GET.get('rating_gte', '')
    year = request.GET.get('year', '')
    ordering = request.GET.get('ordering', '-popularity')
    page = int(request.GET.get('page', 1))
    
    # Django ordering -> TMDB sort_by mapping
    sort_mapping = {
        '-popularity': 'popularity.desc',
        'popularity': 'popularity.asc',
        '-vote_average': 'vote_average.desc',
        'vote_average': 'vote_average.asc',
        '-release_date': 'primary_release_date.desc',
        'release_date': 'primary_release_date.asc',
        'title': 'title.asc',
        '-title': 'title.desc',
    }
    tmdb_sort = sort_mapping.get(ordering, 'popularity.desc')
    
    new_movies = []
    tmdb_total = 0
    
    try:
        tmdb = TMDBService()
        
        # Arama varsa TMDB'den ara
        if search_query and len(search_query) >= 2:
            tmdb_results = tmdb.search_movie(search_query, page=page)
            tmdb_total = tmdb_results.get('total_results', 0)
            
            for movie_data in tmdb_results.get('results', []):
                movie = import_movie_to_db(movie_data)
                if movie:
                    new_movies.append({
                        'id': movie.id,
                        'title': movie.title,
                        'poster_url': movie.poster_url,
                        'vote_average': movie.vote_average,
                        'year': movie.year,
                    })
        
        # Filtre varsa TMDB Discover'dan çek
        elif genre or rating_gte or year:
            # Genre ID'yi TMDB formatına çevir
            tmdb_genre_id = None
            if genre:
                genre_obj = Genre.objects.filter(id=genre).first()
                if genre_obj:
                    tmdb_genre_id = genre_obj.tmdb_id
            
            tmdb_rating = float(rating_gte) if rating_gte else None
            tmdb_year = int(year) if year else None
            
            tmdb_results = tmdb.discover_movies(
                page=page,
                genre_id=tmdb_genre_id,
                year=tmdb_year,
                vote_average_gte=tmdb_rating,
                sort_by=tmdb_sort
            )
            tmdb_total = tmdb_results.get('total_results', 0)
            
            for movie_data in tmdb_results.get('results', []):
                movie = import_movie_to_db(movie_data)
                if movie:
                    new_movies.append({
                        'id': movie.id,
                        'title': movie.title,
                        'poster_url': movie.poster_url,
                        'vote_average': movie.vote_average,
                        'year': movie.year,
                    })
                    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({
        'success': True,
        'movies': new_movies,
        'total': tmdb_total,
    })


def import_movie_to_db(movie_data):
    """TMDB film verisini kütüphaneye ekle (varsa atla), dil fallback ile"""
    from apps.movies.services import tmdb_service
    
    tmdb_id = movie_data.get('id')
    if not tmdb_id:
        return None
    
    # Zaten var mı?
    existing = Movie.objects.filter(tmdb_id=tmdb_id).first()
    if existing:
        # Mevcut film overview boşsa güncellemeyi dene
        if not existing.overview or _is_non_latin(existing.title):
            try:
                full_data = tmdb_service.get_movie_with_fallback(tmdb_id)
                if full_data:
                    if not existing.overview and full_data.get('overview'):
                        existing.overview = full_data.get('overview')
                    if _is_non_latin(existing.title) and full_data.get('title'):
                        existing.title = full_data.get('title')
                    existing.save()
            except Exception as e:
                print(f"Film güncelleme hatası ({tmdb_id}): {e}")
        return existing
    
    try:
        # Tam detayları al (dil fallback ile)
        full_data = tmdb_service.get_movie_with_fallback(tmdb_id)
        
        # Eğer tam detaylar alınamazsa, gelen veriyi kullan
        if full_data:
            title = full_data.get('title', movie_data.get('title', ''))
            overview = full_data.get('overview', movie_data.get('overview', ''))
            runtime = full_data.get('runtime', 0)
            tagline = full_data.get('tagline', '')
        else:
            title = movie_data.get('title', '')
            overview = movie_data.get('overview', '')
            runtime = 0
            tagline = ''
        
        # Temel bilgilerle filmi oluştur
        movie = Movie.objects.create(
            tmdb_id=tmdb_id,
            title=title,
            original_title=movie_data.get('original_title', ''),
            overview=overview,
            tagline=tagline,
            poster_path=movie_data.get('poster_path', ''),
            backdrop_path=movie_data.get('backdrop_path', ''),
            release_date=movie_data.get('release_date') or None,
            vote_average=movie_data.get('vote_average', 0),
            vote_count=movie_data.get('vote_count', 0),
            popularity=movie_data.get('popularity', 0),
            original_language=movie_data.get('original_language', 'en'),
            adult=movie_data.get('adult', False),
            runtime=runtime,
        )
        
        # Türleri ekle
        genre_ids = movie_data.get('genre_ids', []) or (full_data.get('genres', []) if full_data else [])
        for genre_item in genre_ids:
            genre_id = genre_item if isinstance(genre_item, int) else genre_item.get('id')
            if genre_id:
                genre = Genre.objects.filter(tmdb_id=genre_id).first()
                if genre:
                    movie.genres.add(genre)
        
        return movie
    except Exception as e:
        print(f"Film import hatası ({tmdb_id}): {e}")
        return None


def _is_non_latin(text: str) -> bool:
    """Metnin Latin olmayan karakterler içerip içermediğini kontrol et"""
    if not text:
        return False
    latin_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-:;\'"()[]{}@#$%&*+=/<>~`')
    non_latin_count = sum(1 for char in text if char not in latin_chars)
    return non_latin_count > len(text) * 0.3


@login_required
def profile(request):
    """Kullanıcı profili - Detaylı istatistikler"""
    from django.db.models import Count, Avg, Sum
    from collections import Counter
    
    user = request.user
    
    # Temel istatistikler
    ratings = user.ratings.select_related('movie').order_by('-created_at')
    total_ratings = ratings.count()
    avg_rating = ratings.aggregate(Avg('score'))['score__avg'] or 0
    
    # İzlenen filmler istatistikleri
    watched_movies = WatchedMovie.objects.filter(user=user).select_related('movie')
    watched_count = watched_movies.count()
    liked_count = watched_movies.filter(liked=True).count()
    disliked_count = watched_movies.filter(liked=False).count()
    
    # Watchlist sayısı
    watchlist_count = Watchlist.objects.filter(user=user).count()
    
    # Toplam izleme süresi (dakika -> saat)
    total_runtime = watched_movies.filter(
        movie__runtime__isnull=False
    ).aggregate(total=Sum('movie__runtime'))['total'] or 0
    watch_hours = total_runtime // 60
    watch_minutes = total_runtime % 60
    
    # Tür dağılımı (en çok izlenen türler)
    genre_counts = Counter()
    for watched in watched_movies.prefetch_related('movie__genres'):
        for genre in watched.movie.genres.all():
            genre_name = genre.name_tr or genre.name
            genre_counts[genre_name] += 1
    
    # En çok izlenen 8 tür
    top_genres = genre_counts.most_common(8)
    genre_labels = [g[0] for g in top_genres]
    genre_values = [g[1] for g in top_genres]
    
    # Puan dağılımı (histogram için)
    rating_distribution = [0] * 10  # 1-10 arası
    for rating in ratings:
        if 1 <= rating.score <= 10:
            rating_distribution[rating.score - 1] += 1
    
    # Yıllara göre izleme (son 12 ay)
    from datetime import datetime, timedelta
    from django.db.models.functions import TruncMonth
    
    twelve_months_ago = datetime.now() - timedelta(days=365)
    monthly_watches = watched_movies.filter(
        watched_at__gte=twelve_months_ago
    ).annotate(
        month=TruncMonth('watched_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Son 12 ayın etiketleri
    months_labels = []
    months_values = []
    current = datetime.now()
    for i in range(11, -1, -1):
        month_date = current - timedelta(days=i*30)
        months_labels.append(month_date.strftime('%b'))
        # O ay kaç film izlenmiş
        month_count = 0
        for m in monthly_watches:
            if m['month'] and m['month'].month == month_date.month and m['month'].year == month_date.year:
                month_count = m['count']
                break
        months_values.append(month_count)
    
    # Favori yönetmenler
    director_counts = Counter()
    for watched in watched_movies.filter(liked=True).prefetch_related('movie__crew__person'):
        for crew in watched.movie.crew.filter(job='Director'):
            director_counts[crew.person.name] += 1
    top_directors = director_counts.most_common(5)
    
    # Favori oyuncular
    actor_counts = Counter()
    for watched in watched_movies.filter(liked=True).prefetch_related('movie__cast__person'):
        for cast in watched.movie.cast.all()[:5]:  # İlk 5 oyuncu
            actor_counts[cast.person.name] += 1
    top_actors = actor_counts.most_common(5)
    
    # En yüksek puanlanan filmler (kendi puanları)
    top_rated_by_user = ratings.filter(score__gte=8).select_related('movie')[:6]
    
    # Arkadaş sayısı
    friends_count = len(user.get_friends())
    
    context = {
        'user': user,
        'ratings': ratings[:10],
        'total_ratings': total_ratings,
        'avg_rating': round(avg_rating, 1),
        
        # Detaylı istatistikler
        'watched_count': watched_count,
        'liked_count': liked_count,
        'disliked_count': disliked_count,
        'watchlist_count': watchlist_count,
        'watch_hours': watch_hours,
        'watch_minutes': watch_minutes,
        'friends_count': friends_count,
        
        # Grafik verileri (JSON)
        'genre_labels': json.dumps(genre_labels, ensure_ascii=False),
        'genre_values': json.dumps(genre_values),
        'rating_distribution': json.dumps(rating_distribution),
        'months_labels': json.dumps(months_labels),
        'months_values': json.dumps(months_values),
        
        # Listeler
        'top_genres': top_genres,
        'top_directors': top_directors,
        'top_actors': top_actors,
        'top_rated_by_user': top_rated_by_user,
    }
    
    return render(request, 'profile.html', context)


@login_required
def friends(request):
    """Arkadaşlar sayfası"""
    user = request.user
    
    # Arkadaş listesi - avg_rating ekle
    user_friends = user.get_friends()
    for friend in user_friends:
        avg = friend.ratings.aggregate(Avg('score'))['score__avg']
        friend.avg_rating = round(avg, 1) if avg else 0
    
    # Bekleyen istekler (bana gelenler) - avg_rating ekle
    pending_requests = list(user.get_pending_requests())
    for req in pending_requests:
        # Friendship objesi, user alanına avg_rating ekle
        avg = req.user.ratings.aggregate(Avg('score'))['score__avg']
        req.user.avg_rating = round(avg, 1) if avg else 0
    
    # Gönderilen istekler
    sent_requests = user.get_sent_requests()
    
    # Arama
    search_results = []
    search_query = request.GET.get('q', '')
    if search_query and len(search_query) >= 2:
        search_results = list(User.objects.filter(
            Q(username__icontains=search_query) | 
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query)
        ).exclude(id=user.id)[:20])
        
        # Arama sonuçlarına avg_rating ekle
        for result in search_results:
            avg = result.ratings.aggregate(Avg('score'))['score__avg']
            result.avg_rating = round(avg, 1) if avg else 0
    
    context = {
        'friends': user_friends,
        'pending_requests': pending_requests,
        'sent_requests': sent_requests,
        'search_results': search_results,
        'search_query': search_query,
    }
    
    return render(request, 'friends.html', context)


@login_required
@require_POST
def send_friend_request(request):
    """Arkadaşlık isteği gönder"""
    try:
        data = json.loads(request.body)
        friend_username = data.get('friend_username')
        
        if not friend_username:
            return JsonResponse({'success': False, 'error': 'Kullanıcı adı gerekli'}, status=400)
        
        try:
            friend = User.objects.get(username=friend_username)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Kullanıcı bulunamadı'}, status=404)
        
        if friend == request.user:
            return JsonResponse({'success': False, 'error': 'Kendinize istek gönderemezsiniz'}, status=400)
        
        # Mevcut istek var mı?
        existing = Friendship.objects.filter(
            Q(user=request.user, friend=friend) | Q(user=friend, friend=request.user)
        ).first()
        
        if existing:
            if existing.status == 'accepted':
                return JsonResponse({'success': False, 'error': 'Zaten arkadaşsınız'}, status=400)
            elif existing.status == 'pending':
                return JsonResponse({'success': False, 'error': 'Bekleyen istek var'}, status=400)
        
        Friendship.objects.create(user=request.user, friend=friend, status='pending')
        return JsonResponse({'success': True, 'message': f'{friend_username} kullanıcısına istek gönderildi!'})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz istek'}, status=400)


@login_required
@require_POST
def accept_friend_request(request):
    """Arkadaşlık isteğini kabul et"""
    try:
        data = json.loads(request.body)
        friendship_id = data.get('friendship_id')
        
        friendship = get_object_or_404(Friendship, id=friendship_id, friend=request.user, status='pending')
        friendship.accept()
        
        return JsonResponse({'success': True, 'message': f'{friendship.user.username} ile arkadaş oldunuz!'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz istek'}, status=400)


@login_required
@require_POST
def reject_friend_request(request):
    """Arkadaşlık isteğini reddet"""
    try:
        data = json.loads(request.body)
        friendship_id = data.get('friendship_id')
        
        friendship = get_object_or_404(Friendship, id=friendship_id, friend=request.user, status='pending')
        friendship.reject()
        
        return JsonResponse({'success': True, 'message': 'İstek reddedildi'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz istek'}, status=400)


@login_required
@require_POST
def remove_friend(request):
    """Arkadaşı sil"""
    try:
        data = json.loads(request.body)
        friend_username = data.get('friend_username')
        
        friend = get_object_or_404(User, username=friend_username)
        
        friendship = Friendship.objects.filter(
            Q(user=request.user, friend=friend) | Q(user=friend, friend=request.user),
            status='accepted'
        ).first()
        
        if friendship:
            friendship.delete()
            return JsonResponse({'success': True, 'message': f'{friend_username} arkadaşlıktan çıkarıldı'})
        else:
            return JsonResponse({'success': False, 'error': 'Arkadaşlık bulunamadı'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz istek'}, status=400)


@login_required
@require_POST
def add_rating(request):
    """Film puanlama API endpoint"""
    try:
        data = json.loads(request.body)
        movie_id = data.get('movie_id')
        score = data.get('score')
        review = data.get('review', '')
        
        if not movie_id or not score:
            return JsonResponse({'success': False, 'error': 'movie_id ve score gerekli'}, status=400)
        
        if not (1 <= int(score) <= 10):
            return JsonResponse({'success': False, 'error': 'Puan 1-10 arasında olmalı'}, status=400)
        
        movie = get_object_or_404(Movie, id=movie_id)
        
        # Var olan puanı güncelle veya yeni puan oluştur
        rating, created = Rating.objects.update_or_create(
            user=request.user,
            movie=movie,
            defaults={
                'score': int(score),
                'review': review
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Puanınız kaydedildi!' if created else 'Puanınız güncellendi!',
            'rating': {
                'id': rating.id,
                'score': rating.score,
                'review': rating.review,
                'created_at': rating.created_at.strftime('%d %b %Y')
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def edit_profile(request):
    """Profil düzenleme sayfası"""
    if request.method == 'POST':
        user = request.user
        
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        bio = request.POST.get('bio', '')
        date_of_birth = request.POST.get('date_of_birth', '')
        
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.bio = bio
        
        if date_of_birth:
            from datetime import datetime
            try:
                user.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Profil fotoğrafı yükleme
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        return redirect('profile')
    
    return render(request, 'edit_profile.html', {'user': request.user})


@login_required
@require_POST
def toggle_watchlist(request):
    """Watchlist'e ekle/çıkar"""
    try:
        data = json.loads(request.body)
        movie_id = data.get('movie_id')
        
        if not movie_id:
            return JsonResponse({'success': False, 'error': 'movie_id gerekli'}, status=400)
        
        movie = get_object_or_404(Movie, id=movie_id)
        
        # Watchlist'te var mı kontrol et
        watchlist_item = Watchlist.objects.filter(user=request.user, movie=movie).first()
        
        if watchlist_item:
            # Varsa sil
            watchlist_item.delete()
            return JsonResponse({
                'success': True,
                'action': 'removed',
                'message': f'{movie.title} izleme listesinden çıkarıldı'
            })
        else:
            # Yoksa ekle
            Watchlist.objects.create(user=request.user, movie=movie)
            return JsonResponse({
                'success': True,
                'action': 'added',
                'message': f'{movie.title} izleme listesine eklendi'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def mark_as_watched(request):
    """Filmi izlendi olarak işaretle (beğenme/beğenmeme ile)"""
    try:
        data = json.loads(request.body)
        movie_id = data.get('movie_id')
        liked = data.get('liked', True)  # Default: beğenildi
        
        if not movie_id:
            return JsonResponse({'success': False, 'error': 'movie_id gerekli'}, status=400)
        
        movie = get_object_or_404(Movie, id=movie_id)
        
        # WatchedMovie'de var mı kontrol et
        watched, created = WatchedMovie.objects.update_or_create(
            user=request.user,
            movie=movie,
            defaults={'liked': liked}
        )
        
        # Watchlist'ten kaldır (artık izlendi)
        Watchlist.objects.filter(user=request.user, movie=movie).delete()
        
        # Kullanıcı profilini güncelle (tür tercihleri)
        try:
            from apps.recommendations.models import UserTasteProfile
            profile, _ = UserTasteProfile.objects.get_or_create(user=request.user)
            profile.update_from_ratings()
        except Exception:
            pass  # Profil güncelleme opsiyonel
        
        status_text = "beğenildi" if liked else "beğenilmedi"
        return JsonResponse({
            'success': True,
            'action': 'created' if created else 'updated',
            'liked': liked,
            'message': f'{movie.title} izlendi olarak işaretlendi ({status_text})'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def remove_from_watched(request):
    """İzlendi listesinden kaldır"""
    try:
        data = json.loads(request.body)
        movie_id = data.get('movie_id')
        
        if not movie_id:
            return JsonResponse({'success': False, 'error': 'movie_id gerekli'}, status=400)
        
        movie = get_object_or_404(Movie, id=movie_id)
        
        deleted, _ = WatchedMovie.objects.filter(user=request.user, movie=movie).delete()
        
        if deleted:
            return JsonResponse({
                'success': True,
                'action': 'removed',
                'message': f'{movie.title} izlenenlerden kaldırıldı'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Film izlenenler listesinde bulunamadı'
            }, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def watched_movies(request):
    """İzlenen filmler sayfası"""
    filter_type = request.GET.get('filter', 'all')  # all, liked, disliked
    
    watched_items = WatchedMovie.objects.filter(user=request.user).select_related('movie')
    
    if filter_type == 'liked':
        watched_items = watched_items.filter(liked=True)
    elif filter_type == 'disliked':
        watched_items = watched_items.filter(liked=False)
    
    watched_items = watched_items.order_by('-watched_at')
    
    # İstatistikler
    stats = {
        'total': WatchedMovie.objects.filter(user=request.user).count(),
        'liked': WatchedMovie.objects.filter(user=request.user, liked=True).count(),
        'disliked': WatchedMovie.objects.filter(user=request.user, liked=False).count(),
    }
    
    context = {
        'watched_items': watched_items,
        'filter_type': filter_type,
        'stats': stats,
    }
    
    return render(request, 'watched_movies.html', context)


@login_required
def check_movie_status(request, movie_id):
    """Film durumunu kontrol et (watchlist, watched, rating)"""
    movie = get_object_or_404(Movie, id=movie_id)
    
    in_watchlist = Watchlist.objects.filter(user=request.user, movie=movie).exists()
    watched = WatchedMovie.objects.filter(user=request.user, movie=movie).first()
    rating = Rating.objects.filter(user=request.user, movie=movie).first()
    
    return JsonResponse({
        'success': True,
        'movie_id': movie_id,
        'in_watchlist': in_watchlist,
        'is_watched': watched is not None,
        'liked': watched.liked if watched else None,
        'rating': rating.score if rating else None,
    })


@login_required
@require_GET
def search_tmdb(request):
    """TMDB API'den film ara"""
    query = request.GET.get('q', '').strip()
    page = request.GET.get('page', 1)
    
    if not query or len(query) < 2:
        return JsonResponse({'success': False, 'error': 'En az 2 karakter girin'}, status=400)
    
    try:
        tmdb = TMDBService()
        results = tmdb.search_movie(query, page=int(page))
        
        # Hangi filmler zaten veritabanında var?
        tmdb_ids = [m['id'] for m in results.get('results', [])]
        existing_movies = set(Movie.objects.filter(tmdb_id__in=tmdb_ids).values_list('tmdb_id', flat=True))
        
        # Sonuçları işle
        movies = []
        for movie in results.get('results', []):
            movies.append({
                'tmdb_id': movie['id'],
                'title': movie.get('title', ''),
                'original_title': movie.get('original_title', ''),
                'overview': movie.get('overview', '')[:200] + '...' if movie.get('overview') and len(movie.get('overview', '')) > 200 else movie.get('overview', ''),
                'poster_path': f"https://image.tmdb.org/t/p/w300{movie['poster_path']}" if movie.get('poster_path') else None,
                'release_date': movie.get('release_date', ''),
                'vote_average': movie.get('vote_average', 0),
                'in_database': movie['id'] in existing_movies,
            })
        
        return JsonResponse({
            'success': True,
            'results': movies,
            'page': results.get('page', 1),
            'total_pages': results.get('total_pages', 1),
            'total_results': results.get('total_results', 0),
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def import_movie_from_tmdb(request):
    """TMDB'den film detaylarını çekip veritabanına kaydet"""
    try:
        data = json.loads(request.body)
        tmdb_id = data.get('tmdb_id')
        
        if not tmdb_id:
            return JsonResponse({'success': False, 'error': 'tmdb_id gerekli'}, status=400)
        
        # Zaten var mı kontrol et
        existing = Movie.objects.filter(tmdb_id=tmdb_id).first()
        if existing:
            return JsonResponse({
                'success': True,
                'message': 'Film zaten mevcut',
                'movie_id': existing.id,
                'redirect_url': f'/movie/{existing.id}/'
            })
        
        # TMDB'den detayları çek
        tmdb = TMDBService()
        movie_data = tmdb.get_movie_details(tmdb_id)
        
        if not movie_data or 'id' not in movie_data:
            return JsonResponse({'success': False, 'error': 'Film bulunamadı'}, status=404)
        
        # Filmi oluştur
        movie = Movie.objects.create(
            tmdb_id=movie_data['id'],
            imdb_id=movie_data.get('imdb_id', ''),
            title=movie_data.get('title', ''),
            original_title=movie_data.get('original_title', ''),
            overview=movie_data.get('overview', ''),
            tagline=movie_data.get('tagline', ''),
            poster_path=movie_data.get('poster_path', ''),
            backdrop_path=movie_data.get('backdrop_path', ''),
            release_date=movie_data.get('release_date') or None,
            runtime=movie_data.get('runtime'),
            vote_average=movie_data.get('vote_average', 0),
            vote_count=movie_data.get('vote_count', 0),
            popularity=movie_data.get('popularity', 0),
            original_language=movie_data.get('original_language', 'en'),
            status=movie_data.get('status', 'released').lower().replace(' ', '_'),
            adult=movie_data.get('adult', False),
            budget=movie_data.get('budget', 0),
            revenue=movie_data.get('revenue', 0),
            homepage=movie_data.get('homepage', ''),
        )
        
        # Türleri ekle
        for genre_data in movie_data.get('genres', []):
            genre, _ = Genre.objects.get_or_create(
                tmdb_id=genre_data['id'],
                defaults={'name': genre_data['name']}
            )
            movie.genres.add(genre)
        
        # Cast ekle (ilk 10 oyuncu)
        credits = movie_data.get('credits', {})
        for i, cast_data in enumerate(credits.get('cast', [])[:10]):
            person, _ = Person.objects.get_or_create(
                tmdb_id=cast_data['id'],
                defaults={
                    'name': cast_data.get('name', ''),
                    'profile_path': cast_data.get('profile_path', ''),
                    'known_for_department': cast_data.get('known_for_department', ''),
                    'gender': cast_data.get('gender', 0),
                    'popularity': cast_data.get('popularity', 0),
                }
            )
            MovieCast.objects.get_or_create(
                movie=movie,
                person=person,
                defaults={
                    'character_name': cast_data.get('character', ''),
                    'cast_order': i,
                }
            )
        
        # Crew ekle (yönetmenler)
        for crew_data in credits.get('crew', []):
            if crew_data.get('job') == 'Director':
                person, _ = Person.objects.get_or_create(
                    tmdb_id=crew_data['id'],
                    defaults={
                        'name': crew_data.get('name', ''),
                        'profile_path': crew_data.get('profile_path', ''),
                        'known_for_department': crew_data.get('known_for_department', ''),
                        'gender': crew_data.get('gender', 0),
                        'popularity': crew_data.get('popularity', 0),
                    }
                )
                MovieCrew.objects.get_or_create(
                    movie=movie,
                    person=person,
                    job='Director',
                    defaults={'department': 'Directing'}
                )
        
        return JsonResponse({
            'success': True,
            'message': f'{movie.title} başarıyla eklendi!',
            'movie_id': movie.id,
            'redirect_url': f'/movie/{movie.id}/'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================
# PASSWORD RESET VIEWS
# ============================================

def forgot_password(request):
    """Şifremi unuttum sayfası"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            return render(request, 'auth/forgot_password.html', {'error': 'E-posta adresi gerekli'})
        
        try:
            user = User.objects.filter(email=email).first()
            if not user:
                raise User.DoesNotExist()
            
            # Token oluştur
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            from django.conf import settings
            
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Reset URL
            reset_url = f"{settings.SITE_URL}/reset-password/{uid}/{token}/"
            
            # E-posta gönder
            subject = 'MatchFlix - Şifre Sıfırlama'
            message = f'''Merhaba {user.first_name or user.username},

Şifrenizi sıfırlamak için aşağıdaki linke tıklayın:
{reset_url}

Bu link 24 saat geçerlidir.

Eğer bu isteği siz yapmadıysanız, bu e-postayı görmezden gelebilirsiniz.

MatchFlix Ekibi'''
            
            try:
                # HTML template varsa kullan
                html_message = render_to_string('emails/password_reset.html', {
                    'user': user,
                    'reset_url': reset_url,
                    'site_url': settings.SITE_URL,
                })
            except Exception:
                html_message = None
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return render(request, 'auth/forgot_password.html', {
                'success': True,
                'message': 'Şifre sıfırlama linki e-posta adresinize gönderildi.'
            })
            
        except User.DoesNotExist:
            # Güvenlik için kullanıcı bulunamadı demiyoruz
            return render(request, 'auth/forgot_password.html', {
                'success': True,
                'message': 'Eğer bu e-posta adresi kayıtlıysa, şifre sıfırlama linki gönderildi.'
            })
        except Exception as e:
            return render(request, 'auth/forgot_password.html', {
                'error': 'E-posta gönderilirken bir hata oluştu. Lütfen tekrar deneyin.'
            })
    
    return render(request, 'auth/forgot_password.html')


def reset_password(request, uidb64, token):
    """Şifre sıfırlama sayfası"""
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_decode
    
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is None or not default_token_generator.check_token(user, token):
        return render(request, 'auth/reset_password.html', {
            'error': 'Şifre sıfırlama linki geçersiz veya süresi dolmuş.',
            'invalid_link': True
        })
    
    if request.method == 'POST':
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        if not password or len(password) < 8:
            return render(request, 'auth/reset_password.html', {
                'error': 'Şifre en az 8 karakter olmalıdır.',
                'uidb64': uidb64,
                'token': token
            })
        
        if password != password2:
            return render(request, 'auth/reset_password.html', {
                'error': 'Şifreler eşleşmiyor.',
                'uidb64': uidb64,
                'token': token
            })
        
        user.set_password(password)
        user.save()
        
        return render(request, 'auth/reset_password_done.html', {
            'success': True
        })
    
    return render(request, 'auth/reset_password.html', {
        'uidb64': uidb64,
        'token': token
    })


# ============================================
# GOOGLE OAUTH VIEWS
# ============================================

def google_login(request):
    """Google OAuth başlat"""
    from django.conf import settings
    import urllib.parse
    
    if not settings.GOOGLE_OAUTH_CLIENT_ID:
        return render(request, 'login.html', {
            'error': 'Google ile giriş şu an kullanılamıyor.'
        })
    
    # Google OAuth URL oluştur
    params = {
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
        'redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'select_account',
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)


def google_callback(request):
    """Google OAuth callback"""
    import requests
    from django.conf import settings
    
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        return render(request, 'login.html', {
            'error': 'Google ile giriş iptal edildi.'
        })
    
    if not code:
        return render(request, 'login.html', {
            'error': 'Google ile giriş başarısız.'
        })
    
    # Token al
    token_url = 'https://oauth2.googleapis.com/token'
    token_data = {
        'code': code,
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
        'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
        'redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI,
        'grant_type': 'authorization_code',
    }
    
    try:
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'access_token' not in token_json:
            return render(request, 'login.html', {
                'error': 'Google ile giriş başarısız.'
            })
        
        access_token = token_json['access_token']
        
        # Kullanıcı bilgilerini al
        userinfo_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        userinfo_response = requests.get(userinfo_url, headers=headers)
        userinfo = userinfo_response.json()
        
        email = userinfo.get('email')
        google_id = userinfo.get('id')
        first_name = userinfo.get('given_name', '')
        last_name = userinfo.get('family_name', '')
        picture = userinfo.get('picture', '')
        
        if not email:
            return render(request, 'login.html', {
                'error': 'Google hesabından e-posta alınamadı.'
            })
        
        # Kullanıcıyı bul veya oluştur
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'first_name': first_name,
                'last_name': last_name,
            }
        )
        
        # İsim güncelle (varsa)
        if not created and (not user.first_name or not user.last_name):
            user.first_name = first_name or user.first_name
            user.last_name = last_name or user.last_name
            user.save()
        
        # Giriş yap
        auth_login(request, user)
        
        # Yeni kullanıcıysa onboarding'e yönlendir
        if created or not user.onboarding_completed:
            return redirect('onboarding')
        
        return redirect('home')
        
    except Exception as e:
        return render(request, 'login.html', {
            'error': f'Google ile giriş sırasında bir hata oluştu.'
        })


# ============================================================================
# ONBOARDING
# ============================================================================

@login_required
def onboarding(request):
    """Yeni kullanıcı onboarding sayfası - Film ve tür seçimi"""
    
    # Zaten tamamladıysa ana sayfaya yönlendir
    if request.user.onboarding_completed:
        return redirect('home')
    
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Film puanlarını kaydet
        ratings_data = data.get('ratings', [])
        for rating_item in ratings_data:
            movie_id = rating_item.get('movie_id')
            score = rating_item.get('score')  # 1-10 arası
            
            if movie_id and score:
                try:
                    movie = Movie.objects.get(id=movie_id)
                    Rating.objects.update_or_create(
                        user=request.user,
                        movie=movie,
                        defaults={'score': score}
                    )
                    
                    # İzlendi olarak da işaretle
                    WatchedMovie.objects.get_or_create(
                        user=request.user,
                        movie=movie,
                        defaults={'liked': score >= 6}
                    )
                except Movie.DoesNotExist:
                    pass
        
        # Favori türleri kaydet
        genre_ids = data.get('genres', [])
        if genre_ids:
            genres = Genre.objects.filter(id__in=genre_ids)
            request.user.favorite_genres.set(genres)
        
        # Kullanıcı profilini güncelle
        try:
            from apps.recommendations.models import UserTasteProfile
            profile, _ = UserTasteProfile.objects.get_or_create(user=request.user)
            profile.update_from_ratings()
        except Exception:
            pass
        
        # Onboarding'i tamamla
        request.user.onboarding_completed = True
        request.user.save()
        
        return JsonResponse({'success': True, 'redirect': '/home/'})
    
    # GET request - Sayfayı göster
    # Çeşitli kategorilerden filmler hazırla
    base_query = Movie.objects.filter(
        poster_path__isnull=False
    ).exclude(poster_path='')
    
    movie_categories = []
    seen_ids = set()
    
    # 1. En Yüksek Puanlı (Herkesin bildiği klasikler)
    top_rated = base_query.filter(
        vote_average__gte=8.0,
        vote_count__gte=1000
    ).order_by('-vote_average')[:15]
    
    category_movies = []
    for m in top_rated:
        if m.id not in seen_ids:
            category_movies.append(m)
            seen_ids.add(m.id)
    movie_categories.append({
        'name': 'Efsaneler',
        'emoji': '👑',
        'movies': category_movies[:12]
    })
    
    # 2. Popüler Yeni Filmler (2020+)
    recent_popular = base_query.filter(
        release_date__year__gte=2020,
        vote_count__gte=500
    ).order_by('-popularity')[:15]
    
    category_movies = []
    for m in recent_popular:
        if m.id not in seen_ids:
            category_movies.append(m)
            seen_ids.add(m.id)
    movie_categories.append({
        'name': 'Yeni Çıkanlar',
        'emoji': '🆕',
        'movies': category_movies[:12]
    })
    
    # 3. Aksiyon & Macera
    action_movies = base_query.filter(
        genres__tmdb_id__in=[28, 12],  # Action, Adventure
        vote_average__gte=7.0
    ).distinct().order_by('-popularity')[:15]
    
    category_movies = []
    for m in action_movies:
        if m.id not in seen_ids:
            category_movies.append(m)
            seen_ids.add(m.id)
    movie_categories.append({
        'name': 'Aksiyon & Macera',
        'emoji': '💥',
        'movies': category_movies[:12]
    })
    
    # 4. Komedi
    comedy_movies = base_query.filter(
        genres__tmdb_id=35,  # Comedy
        vote_average__gte=6.5
    ).distinct().order_by('-popularity')[:15]
    
    category_movies = []
    for m in comedy_movies:
        if m.id not in seen_ids:
            category_movies.append(m)
            seen_ids.add(m.id)
    movie_categories.append({
        'name': 'Komedi',
        'emoji': '😂',
        'movies': category_movies[:12]
    })
    
    # 5. Dram & Romantik
    drama_movies = base_query.filter(
        genres__tmdb_id__in=[18, 10749],  # Drama, Romance
        vote_average__gte=7.0
    ).distinct().order_by('-vote_average')[:15]
    
    category_movies = []
    for m in drama_movies:
        if m.id not in seen_ids:
            category_movies.append(m)
            seen_ids.add(m.id)
    movie_categories.append({
        'name': 'Dram & Romantik',
        'emoji': '💔',
        'movies': category_movies[:12]
    })
    
    # 6. Bilim Kurgu & Fantastik
    scifi_movies = base_query.filter(
        genres__tmdb_id__in=[878, 14],  # Sci-Fi, Fantasy
        vote_average__gte=7.0
    ).distinct().order_by('-popularity')[:15]
    
    category_movies = []
    for m in scifi_movies:
        if m.id not in seen_ids:
            category_movies.append(m)
            seen_ids.add(m.id)
    movie_categories.append({
        'name': 'Bilim Kurgu & Fantastik',
        'emoji': '🚀',
        'movies': category_movies[:12]
    })
    
    # Tüm türler
    genres = Genre.objects.all().order_by('name_tr', 'name')
    
    context = {
        'movie_categories': movie_categories,
        'genres': genres,
    }
    
    return render(request, 'onboarding.html', context)


@login_required
def skip_onboarding(request):
    """Onboarding'i atla"""
    request.user.onboarding_completed = True
    request.user.save()
    return redirect('home')
