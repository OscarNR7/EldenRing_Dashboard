import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import './ArmorCard.css';

const ArmorCard = ({ armor }) => {
  return (
    <Card className="armor-card">
      <CardHeader className="armor-card-header">
        <CardTitle className="armor-card-title">{armor.name}</CardTitle>
      </CardHeader>
      <CardContent className="armor-card-content">
        {armor.image && <img src={armor.image} alt={armor.name} className="armor-card-image" />}
        {!armor.image && <div className="armor-card-image-placeholder">No Image</div>}
        <div className="armor-card-details">
          {armor.category && <p><strong>Categoría:</strong> {armor.category}</p>}
          {armor.weight && <p><strong>Peso:</strong> {armor.weight}</p>}
        </div>
      </CardContent>
    </Card>
  );
};

export default ArmorCard;
