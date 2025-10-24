import React from 'react';
import './WeaponCard.css';

const WeaponCard = ({ weapon }) => {
  return (
    <div className="weapon-card">
      {weapon.image && (
        <div className="weapon-card-image">
          <img src={weapon.image} alt={weapon.name} />
        </div>
      )}
      <div className="weapon-card-content">
        <h3 className="weapon-name">{weapon.name}</h3>
        {weapon.category && (
          <p className="weapon-category">{weapon.category}</p>
        )}
        {weapon.weight && (
          <p className="weapon-stat">
            <span className="stat-label">Peso:</span> {weapon.weight}
          </p>
        )}
        {weapon.attack?.physical && (
          <p className="weapon-stat">
            <span className="stat-label">Daño físico:</span> {weapon.attack.physical}
          </p>
        )}
        {weapon.requiredAttributes && (
          <div className="weapon-requirements">
            <p className="stat-label">Requisitos:</p>
            <div className="requirements-grid">
              {weapon.requiredAttributes.strength > 0 && (
                <span>FUE: {weapon.requiredAttributes.strength}</span>
              )}
              {weapon.requiredAttributes.dexterity > 0 && (
                <span>DES: {weapon.requiredAttributes.dexterity}</span>
              )}
              {weapon.requiredAttributes.intelligence > 0 && (
                <span>INT: {weapon.requiredAttributes.intelligence}</span>
              )}
              {weapon.requiredAttributes.faith > 0 && (
                <span>FE: {weapon.requiredAttributes.faith}</span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WeaponCard;
