import React from 'react';
import BossCard from './BossCard';
import './BossGrid.css';

const BossGrid = ({ bosses }) => {
  if (!bosses || bosses.length === 0) {
    return <p className="no-results">No se encontraron jefes con los filtros aplicados.</p>;
  }

  return (
    <div className="boss-grid">
      {bosses.map(boss => (
        <BossCard key={boss.id} boss={boss} />
      ))}
    </div>
  );
};

export default BossGrid;
