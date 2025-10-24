import React from 'react';
import './Footer.css';

const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-container">
        <p>&copy; {new Date().getFullYear()} Compendio de Elden Ring. Todos los derechos reservados.</p>
        <p>Hecho con ❤️ para los Tarnished.</p>
      </div>
    </footer>
  );
};

export default Footer;
