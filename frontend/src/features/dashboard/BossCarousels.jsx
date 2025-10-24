import React from 'react';
import BossCard from '../../features/bosses/BossCard';
import './BossCarousels.css';

const BossCarousels = ({ bosses }) => {
  // Asegurarse de que bosses sea un array antes de filtrar
  const bossesArray = Array.isArray(bosses) ? bosses : (bosses && bosses.items ? bosses.items : []);

  // Filtrar explícitamente por true, asegurando que el valor sea booleano
  const greatRuneBosses = bossesArray.filter(boss => !!boss.has_great_rune === true);
  const remembranceBosses = bossesArray.filter(boss => !!boss.has_remembrance === true);

  return (
    <div className="boss-carousels-container">
      <h2 className="carousel-section-title">Portadores de Grandes Runas</h2>
      {greatRuneBosses.length > 0 ? (
        <div className="carousel">
          {greatRuneBosses.map(boss => (
            <BossCard key={boss.id} boss={boss} />
          ))}
        </div>
      ) : (
        <p className="no-data-message">No se encontraron jefes con Grandes Runas.</p>
      )}

      <h2 className="carousel-section-title">Portadores de Remembrances</h2>
      {remembranceBosses.length > 0 ? (
        <div className="carousel">
          {remembranceBosses.map(boss => (
            <BossCard key={boss.id} boss={boss} />
          ))}
        </div>
      ) : (
        <p className="no-data-message">No se encontraron jefes con Remembrances.</p>
      )}
    </div>
  );
};

export default BossCarousels;