import React, { useState } from 'react';
import './WeaponFilter.css';

const WeaponFilter = ({ onFilterChange }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const handleInputChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleSearch = () => {
    const cleanFilters = searchTerm.trim() ? { name: searchTerm.trim() } : {};
    onFilterChange(cleanFilters);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleClear = () => {
    setSearchTerm('');
    onFilterChange({});
  };

  return (
    <div className="weapon-filter-container">
      <div className="filter-group search-group">
        <label htmlFor="name">Buscar arma:</label>
        <input
          type="text"
          id="name"
          name="name"
          value={searchTerm}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          placeholder="Escribe el nombre del arma..."
        />
      </div>

      <button className="search-btn" onClick={handleSearch}>
        Buscar
      </button>
      
      {searchTerm && (
        <button className="clear-btn" onClick={handleClear}>
          Limpiar
        </button>
      )}
    </div>
  );
};

export default WeaponFilter;
