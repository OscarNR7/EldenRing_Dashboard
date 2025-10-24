import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import './ClassCard.css';

const ClassCard = ({ classData }) => {
  return (
    <Card className="class-card">
      <CardHeader className="class-card-header">
        <CardTitle className="class-card-title">{classData.name}</CardTitle>
      </CardHeader>
      <CardContent className="class-card-content">
        {classData.image && <img src={classData.image} alt={classData.name} className="class-card-image" />}
        {!classData.image && <div className="class-card-image-placeholder">No Image</div>}
        <div className="class-card-details">
          {classData.stats && (
            <>
              <p><strong>Nivel:</strong> {classData.stats.level}</p>
              <p><strong>Vigor:</strong> {classData.stats.vigor}</p>
              <p><strong>Mente:</strong> {classData.stats.mind}</p>
              <p><strong>Fuerza:</strong> {classData.stats.strength}</p>
              <p><strong>Destreza:</strong> {classData.stats.dexterity}</p>
              <p><strong>Inteligencia:</strong> {classData.stats.intelligence}</p>
              <p><strong>Fe:</strong> {classData.stats.faith}</p>
              <p><strong>Arcano:</strong> {classData.stats.arcane}</p>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default ClassCard;
