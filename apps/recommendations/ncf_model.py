"""
Neural Collaborative Filtering Model
=====================================
PyTorch tabanlı NCF öneri modeli
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Optional, Tuple, List


class NCFModel(nn.Module):
    """
    Neural Collaborative Filtering
    GMF (Generalized Matrix Factorization) + MLP kombinasyonu
    """
    
    def __init__(
        self,
        num_users: int,
        num_items: int,
        embedding_dim: int = 64,
        mlp_layers: List[int] = [128, 64, 32],
        dropout: float = 0.2
    ):
        super(NCFModel, self).__init__()
        
        self.num_users = num_users
        self.num_items = num_items
        self.embedding_dim = embedding_dim
        
        # GMF embeddings
        self.user_embedding_gmf = nn.Embedding(num_users, embedding_dim)
        self.item_embedding_gmf = nn.Embedding(num_items, embedding_dim)
        
        # MLP embeddings
        self.user_embedding_mlp = nn.Embedding(num_users, embedding_dim)
        self.item_embedding_mlp = nn.Embedding(num_items, embedding_dim)
        
        # MLP layers
        mlp_input_dim = embedding_dim * 2
        layers = []
        for i, hidden_dim in enumerate(mlp_layers):
            layers.append(nn.Linear(mlp_input_dim if i == 0 else mlp_layers[i-1], hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.BatchNorm1d(hidden_dim))
            layers.append(nn.Dropout(dropout))
        self.mlp = nn.Sequential(*layers)
        
        # NeuMF layer - GMF output + MLP output
        neumf_input_dim = embedding_dim + mlp_layers[-1]
        self.neumf = nn.Sequential(
            nn.Linear(neumf_input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
        self._init_weights()
    
    def _init_weights(self):
        """Xavier initialization"""
        for module in self.modules():
            if isinstance(module, nn.Embedding):
                nn.init.xavier_normal_(module.weight)
            elif isinstance(module, nn.Linear):
                nn.init.xavier_normal_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
    
    def forward(self, user_ids: torch.Tensor, item_ids: torch.Tensor) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            user_ids: (batch_size,) user indices
            item_ids: (batch_size,) item indices
        
        Returns:
            predictions: (batch_size,) predicted ratings (0-1)
        """
        # GMF path
        user_gmf = self.user_embedding_gmf(user_ids)
        item_gmf = self.item_embedding_gmf(item_ids)
        gmf_output = user_gmf * item_gmf  # Element-wise product
        
        # MLP path
        user_mlp = self.user_embedding_mlp(user_ids)
        item_mlp = self.item_embedding_mlp(item_ids)
        mlp_input = torch.cat([user_mlp, item_mlp], dim=1)
        mlp_output = self.mlp(mlp_input)
        
        # NeuMF
        neumf_input = torch.cat([gmf_output, mlp_output], dim=1)
        prediction = self.neumf(neumf_input)
        
        return prediction.squeeze()
    
    def predict(self, user_id: int, item_ids: List[int]) -> np.ndarray:
        """
        Tek kullanıcı için birden fazla item tahmini
        """
        self.eval()
        with torch.no_grad():
            user_tensor = torch.tensor([user_id] * len(item_ids))
            item_tensor = torch.tensor(item_ids)
            predictions = self.forward(user_tensor, item_tensor)
            return predictions.numpy()
    
    def get_user_embedding(self, user_id: int) -> np.ndarray:
        """Kullanıcı embedding vektörünü al"""
        self.eval()
        with torch.no_grad():
            user_tensor = torch.tensor([user_id])
            gmf_emb = self.user_embedding_gmf(user_tensor)
            mlp_emb = self.user_embedding_mlp(user_tensor)
            combined = torch.cat([gmf_emb, mlp_emb], dim=1)
            return combined.numpy().flatten()
    
    def get_item_embedding(self, item_id: int) -> np.ndarray:
        """Item embedding vektörünü al"""
        self.eval()
        with torch.no_grad():
            item_tensor = torch.tensor([item_id])
            gmf_emb = self.item_embedding_gmf(item_tensor)
            mlp_emb = self.item_embedding_mlp(item_tensor)
            combined = torch.cat([gmf_emb, mlp_emb], dim=1)
            return combined.numpy().flatten()


class NCFTrainer:
    """NCF Model eğitimi"""
    
    def __init__(
        self,
        model: NCFModel,
        learning_rate: float = 0.001,
        weight_decay: float = 1e-5
    ):
        self.model = model
        self.optimizer = torch.optim.Adam(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        self.criterion = nn.BCELoss()
    
    def _train_batch(self, batch: dict, device: str = 'cpu') -> float:
        """Tek batch eğitimi"""
        self.model.train()
        self.model.to(device)
        
        user_ids = batch['user_id'].to(device)
        item_ids = batch['item_id'].to(device)
        labels = batch['label'].float().to(device)
        
        self.optimizer.zero_grad()
        predictions = self.model(user_ids, item_ids)
        loss = self.criterion(predictions, labels)
        loss.backward()
        self.optimizer.step()
        
        return loss.item()
    
    def train_epoch(
        self,
        train_loader: torch.utils.data.DataLoader,
        device: str = 'cpu'
    ) -> float:
        """Bir epoch eğitim"""
        self.model.train()
        self.model.to(device)
        
        total_loss = 0.0
        for batch in train_loader:
            loss = self._train_batch(batch, device)
            total_loss += loss
        
        return total_loss / len(train_loader)
    
    def evaluate(
        self,
        test_loader: torch.utils.data.DataLoader,
        device: str = 'cpu'
    ) -> Tuple[float, float]:
        """Model değerlendirme"""
        self.model.eval()
        self.model.to(device)
        
        total_loss = 0.0
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for batch in test_loader:
                user_ids = batch['user_id'].to(device)
                item_ids = batch['item_id'].to(device)
                labels = batch['label'].float().to(device)
                
                predictions = self.model(user_ids, item_ids)
                loss = self.criterion(predictions, labels)
                
                total_loss += loss.item()
                all_preds.extend(predictions.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        avg_loss = total_loss / len(test_loader)
        
        # AUC hesapla
        from sklearn.metrics import roc_auc_score
        try:
            auc = roc_auc_score(all_labels, all_preds)
        except ValueError:
            auc = 0.5
        
        return avg_loss, auc
    
    def save(self, path: str):
        """Modeli kaydet"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'num_users': self.model.num_users,
            'num_items': self.model.num_items,
            'embedding_dim': self.model.embedding_dim,
        }, path)
    
    @classmethod
    def load(cls, path: str) -> 'NCFTrainer':
        """Modeli yükle"""
        checkpoint = torch.load(path, map_location='cpu')
        
        model = NCFModel(
            num_users=checkpoint['num_users'],
            num_items=checkpoint['num_items'],
            embedding_dim=checkpoint['embedding_dim']
        )
        model.load_state_dict(checkpoint['model_state_dict'])
        
        trainer = cls(model)
        trainer.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        return trainer

