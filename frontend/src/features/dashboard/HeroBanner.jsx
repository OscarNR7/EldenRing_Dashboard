import React from 'react';
import './HeroBanner.css';

const HeroBanner = () => {
  return (
    <div className="hero-banner">
      <img src="/images/2.png" alt="Elden Ring Banner" className="hero-banner-image" />
      <div className="hero-banner-overlay">
        <h1 className="hero-banner-title">Explora las Tierras Intermedias</h1>
        <p className="hero-banner-description">Descubre estadísticas, armas, armaduras y jefes de Elden Ring.</p>
      </div>
    </div>
  );
};

export default HeroBanner;
