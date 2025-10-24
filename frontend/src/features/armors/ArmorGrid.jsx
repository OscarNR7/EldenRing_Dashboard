import React from 'react';
import ArmorCard from './ArmorCard';
import './ArmorGrid.css';

const ArmorGrid = ({ armors }) => {
  if (!armors || armors.length === 0) {
    return <p className="no-results">No se encontraron armaduras con los filtros aplicados.</p>;
  }

  return (
    <div className="armor-grid">
      {armors.map(armor => (
        <ArmorCard key={armor.id} armor={armor} />
      ))}
    </div>
  );
};

export default ArmorGrid;
