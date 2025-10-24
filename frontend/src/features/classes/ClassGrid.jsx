import React from 'react';
import ClassCard from './ClassCard';
import './ClassGrid.css';

const ClassGrid = ({ classes }) => {
  if (!classes || classes.length === 0) {
    return <p className="no-results">No se encontraron clases.</p>;
  }

  return (
    <div className="class-grid">
      {classes.map(classData => (
        <ClassCard key={classData.id} classData={classData} />
      ))}
    </div>
  );
};

export default ClassGrid;
