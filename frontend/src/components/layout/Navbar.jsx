import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import './Navbar.css';

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          <img src="/images/rune_icon.png" alt="Elden Ring Logo" className="navbar-logo" />
          <span className="navbar-title">Elden Ring Dashboard</span>
        </Link>
        <ul className="nav-links">
          <li>
            <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
              Inicio
            </NavLink>
          </li>
          <li>
            <NavLink to="/weapons" className={({ isActive }) => isActive ? 'active' : ''}>
              Armas
            </NavLink>
          </li>
          <li>
            <NavLink to="/bosses" className={({ isActive }) => isActive ? 'active' : ''}>
              Jefes
            </NavLink>
          </li>
          <li>
            <NavLink to="/armors" className={({ isActive }) => isActive ? 'active' : ''}>
              Armaduras
            </NavLink>
          </li>
          <li>
            <NavLink to="/classes" className={({ isActive }) => isActive ? 'active' : ''}>
              Clases
            </NavLink>
          </li>
          {/* <li>
            <NavLink to="/tools/comparator" className={({ isActive }) => isActive ? 'active' : ''}>
              Herramientas
            </NavLink>
          </li> */}
        </ul>
      </div>
    </nav>
  );
};

export default Navbar;