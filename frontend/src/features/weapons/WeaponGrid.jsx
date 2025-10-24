import React from 'react';
import WeaponCard from './WeaponCard';
import './WeaponGrid.css';

const WeaponGrid = ({ weapons }) => {
  if (!weapons || weapons.length === 0) {
    return <p className="no-results">No se encontraron armas con los filtros aplicados.</p>;
  }

  return (
    <div className="weapon-grid">
      {weapons.map(weapon => (
        <WeaponCard key={weapon.id || weapon._id} weapon={weapon} />
      ))}
    </div>
  );
};

export default WeaponGrid;
