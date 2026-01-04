"""
NCF Model Egitimi (Optimized)
==============================
MovieLens verileriyle Neural Collaborative Filtering modeli egit
- Sampling destegi (buyuk veri setleri icin)
- Progress bar
- Optimize edilmis veri yukleme
"""

import os
import pickle
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset
from django.core.management.base import BaseCommand
from apps.recommendations.models import MovieLensMapping
from apps.recommendations.ncf_model import NCFModel, NCFTrainer


class RatingsDataset(Dataset):
    """Optimized MovieLens ratings dataset"""
    
    def __init__(self, user_ids, item_ids, labels):
        self.user_ids = torch.tensor(user_ids, dtype=torch.long)
        self.item_ids = torch.tensor(item_ids, dtype=torch.long)
        self.labels = torch.tensor(labels, dtype=torch.float32)
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        return {
            'user_id': self.user_ids[idx],
            'item_id': self.item_ids[idx],
            'label': self.labels[idx]
        }


class Command(BaseCommand):
    help = 'Train NCF recommendation model using MovieLens data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--ratings-path',
            type=str,
            required=True,
            help='Path to ratings.csv file'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='ncf_model.pkl',
            help='Output model file path'
        )
        parser.add_argument(
            '--epochs',
            type=int,
            default=5,
            help='Number of training epochs'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1024,
            help='Batch size'
        )
        parser.add_argument(
            '--embedding-dim',
            type=int,
            default=64,
            help='Embedding dimension'
        )
        parser.add_argument(
            '--max-ratings',
            type=int,
            default=1000000,
            help='Maximum number of ratings to use (sampling)'
        )
        parser.add_argument(
            '--negative-ratio',
            type=int,
            default=2,
            help='Negative samples per positive sample'
        )
    
    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*60)
        self.stdout.write("NCF MODEL EGITIMI")
        self.stdout.write("="*60 + "\n")
        
        # 1. Ratings yukle
        self.stdout.write("[1/5] MovieLens ratings yukleniyor...")
        ratings_df = pd.read_csv(options['ratings_path'])
        self.stdout.write(f"      Toplam rating: {len(ratings_df):,}")
        
        # 2. Sadece eslesen filmleri al
        self.stdout.write("\n[2/5] Eslesen filmler filtreleniyor...")
        valid_ml_ids = set(
            MovieLensMapping.objects.filter(movie__isnull=False)
            .values_list('movielens_id', flat=True)
        )
        
        if not valid_ml_ids:
            self.stderr.write(
                "[ERROR] Eslesen film bulunamadi. Once import_movielens calistirin."
            )
            return
        
        ratings_df = ratings_df[ratings_df['movieId'].isin(valid_ml_ids)]
        self.stdout.write(f"      Eslesen rating: {len(ratings_df):,}")
        
        # 3. Sampling (cok buyuk veri setleri icin)
        max_ratings = options['max_ratings']
        if len(ratings_df) > max_ratings:
            self.stdout.write(f"      Sampling: {max_ratings:,} rating seciliyor...")
            ratings_df = ratings_df.sample(n=max_ratings, random_state=42)
        
        # 4. User ve Item mapping
        self.stdout.write("\n[3/5] Mapping olusturuluyor...")
        unique_users = ratings_df['userId'].unique()
        unique_items = ratings_df['movieId'].unique()
        
        user_map = {uid: idx for idx, uid in enumerate(unique_users)}
        item_map = {iid: idx for idx, iid in enumerate(unique_items)}
        
        # Reverse mapping (model kullanimi icin)
        reverse_item_map = {idx: iid for iid, idx in item_map.items()}
        
        num_users = len(unique_users)
        num_items = len(unique_items)
        
        self.stdout.write(f"      Kullanici: {num_users:,}")
        self.stdout.write(f"      Film: {num_items:,}")
        
        # 5. Dataset olustur (vectorized)
        self.stdout.write("\n[4/5] Dataset hazirlaniyor...")
        
        # Positive samples
        user_ids = ratings_df['userId'].map(user_map).values
        item_ids = ratings_df['movieId'].map(item_map).values
        
        # User-item interaction matrix (negative sampling icin)
        user_items = {}
        for u, i in zip(user_ids, item_ids):
            if u not in user_items:
                user_items[u] = set()
            user_items[u].add(i)
        
        # Negative sampling
        self.stdout.write("      Negative sampling yapiliyor...")
        neg_ratio = options['negative_ratio']
        all_items = set(range(num_items))
        
        neg_user_ids = []
        neg_item_ids = []
        
        for u in user_items:
            positive_items = user_items[u]
            negative_items = list(all_items - positive_items)
            
            n_neg = min(len(positive_items) * neg_ratio, len(negative_items))
            if n_neg > 0:
                sampled_neg = np.random.choice(negative_items, size=n_neg, replace=False)
                neg_user_ids.extend([u] * n_neg)
                neg_item_ids.extend(sampled_neg)
        
        # Birlestir
        all_user_ids = np.concatenate([user_ids, np.array(neg_user_ids)])
        all_item_ids = np.concatenate([item_ids, np.array(neg_item_ids)])
        all_labels = np.concatenate([
            np.ones(len(user_ids)),
            np.zeros(len(neg_user_ids))
        ])
        
        # Shuffle
        shuffle_idx = np.random.permutation(len(all_labels))
        all_user_ids = all_user_ids[shuffle_idx]
        all_item_ids = all_item_ids[shuffle_idx]
        all_labels = all_labels[shuffle_idx]
        
        # Train/Test split
        split_idx = int(0.8 * len(all_labels))
        
        train_dataset = RatingsDataset(
            all_user_ids[:split_idx],
            all_item_ids[:split_idx],
            all_labels[:split_idx]
        )
        test_dataset = RatingsDataset(
            all_user_ids[split_idx:],
            all_item_ids[split_idx:],
            all_labels[split_idx:]
        )
        
        train_loader = DataLoader(
            train_dataset, 
            batch_size=options['batch_size'], 
            shuffle=True,
            num_workers=0
        )
        test_loader = DataLoader(
            test_dataset, 
            batch_size=options['batch_size'],
            num_workers=0
        )
        
        self.stdout.write(f"      Train: {len(train_dataset):,} sample")
        self.stdout.write(f"      Test: {len(test_dataset):,} sample")
        
        # 6. Model olustur ve egit
        self.stdout.write("\n[5/5] Model egitiliyor...")
        
        model = NCFModel(
            num_users=num_users,
            num_items=num_items,
            embedding_dim=options['embedding_dim'],
            mlp_layers=[128, 64, 32],
            dropout=0.2
        )
        
        trainer = NCFTrainer(model, learning_rate=0.001)
        
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.stdout.write(f"      Device: {device}")
        self.stdout.write(f"      Epochs: {options['epochs']}")
        self.stdout.write("")
        
        best_auc = 0
        total_batches = len(train_loader)
        
        for epoch in range(options['epochs']):
            # Training with progress
            model.train()
            epoch_loss = 0
            
            for batch_idx, batch in enumerate(train_loader):
                loss = trainer._train_batch(batch, device)
                epoch_loss += loss
                
                # Progress her 100 batch'te bir
                if (batch_idx + 1) % 100 == 0:
                    progress = (batch_idx + 1) / total_batches * 100
                    self.stdout.write(
                        f"\r      Epoch {epoch+1}/{options['epochs']} - "
                        f"[{'#' * int(progress/5)}{' ' * (20-int(progress/5))}] "
                        f"{progress:.1f}%",
                        ending=''
                    )
                    self.stdout.flush()
            
            train_loss = epoch_loss / len(train_loader)
            
            # Evaluation
            test_loss, test_auc = trainer.evaluate(test_loader, device)
            
            self.stdout.write(
                f"\r      Epoch {epoch+1}/{options['epochs']} - "
                f"Train Loss: {train_loss:.4f}, "
                f"Test Loss: {test_loss:.4f}, "
                f"AUC: {test_auc:.4f}"
            )
            
            if test_auc > best_auc:
                best_auc = test_auc
                trainer.save(options['output'])
                self.stdout.write(f"      >> Yeni best model kaydedildi! (AUC: {test_auc:.4f})")
        
        # Mapping bilgilerini kaydet
        mapping_path = options['output'].replace('.pkl', '_mappings.pkl')
        with open(mapping_path, 'wb') as f:
            pickle.dump({
                'user_map': user_map,
                'item_map': item_map,
                'reverse_item_map': reverse_item_map,
                'num_users': num_users,
                'num_items': num_items,
            }, f)
        
        # MovieLens ID -> Our Movie ID mapping
        ml_to_movie = dict(
            MovieLensMapping.objects.filter(movie__isnull=False)
            .values_list('movielens_id', 'movie_id')
        )
        
        ml_mapping_path = options['output'].replace('.pkl', '_ml_mapping.pkl')
        with open(ml_mapping_path, 'wb') as f:
            pickle.dump({
                'item_map': item_map,  # MovieLens ID -> Model index
                'ml_to_movie': ml_to_movie,  # MovieLens ID -> Our DB Movie ID
            }, f)
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("EGITIM TAMAMLANDI!"))
        self.stdout.write(f"   Best AUC: {best_auc:.4f}")
        self.stdout.write(f"   Model: {options['output']}")
        self.stdout.write(f"   Mappings: {mapping_path}")
        self.stdout.write("="*60 + "\n")
