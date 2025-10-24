import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import './BossCard.css';

const BossCard = ({ boss }) => {
  return (
    <Card className="boss-card">
      <CardHeader className="boss-card-header">
        <CardTitle className="boss-card-title">{boss.name}</CardTitle>
      </CardHeader>
      <CardContent className="boss-card-content">
        {boss.image && <img src={boss.image} alt={boss.name} className="boss-card-image" />}
        {!boss.image && <div className="boss-card-image-placeholder">No Image</div>}
        <div className="boss-card-details">
          {boss.region && <p><strong>Región:</strong> {boss.region}</p>}
          {boss.boss_tier && <p><strong>Tier:</strong> {boss.boss_tier}</p>}
        </div>
      </CardContent>
    </Card>
  );
};

export default BossCard;