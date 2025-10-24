import React, { useState, useEffect, useCallback } from 'react';
import useFetchData from '../../hooks/useFetchData';
import { getArmors } from '../../lib/armorService';
import LoadingSpinner from '../../components/LoadingSpinner';
import ArmorFilter from '../../features/armors/ArmorFilter';
import ArmorGrid from '../../features/armors/ArmorGrid';

const ExploreArmorsPage = () => {
  const [filters, setFilters] = useState({});
  const [pagination, setPagination] = useState({ skip: 0, limit: 20 });
  const { data, loading, error, execute } = useFetchData();

  const fetchArmors = useCallback(async () => {
    const params = { ...filters, ...pagination };
    const result = await getArmors(params);
    return result;
  }, [filters, pagination]);

  // Carga inicial de datos al montar el componente
  useEffect(() => {
    execute(fetchArmors);
  }, []);

  // Solo hace fetch cuando el usuario pulsa 'Buscar'
  const handleFilterChange = useCallback((newFilters) => {
    setFilters(newFilters);
    setPagination({ skip: 0, limit: 20 }); // Resetear paginación
    execute(async () => {
      const params = { ...newFilters, skip: 0, limit: 20 };
      return await getArmors(params);
    });
  }, [execute]);

  const handlePageChange = useCallback((newPage) => {
    const newSkip = (newPage - 1) * pagination.limit;
    setPagination(prev => ({ ...prev, skip: newSkip }));
    execute(async () => {
      const params = { ...filters, skip: newSkip, limit: pagination.limit };
      return await getArmors(params);
    });
  }, [execute, filters, pagination.limit]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <div className="container">Error: {error.message}</div>;
  }

  const currentPage = Math.floor(pagination.skip / pagination.limit) + 1;
  const totalItems = data?.total || 0;
  const totalPages = Math.ceil(totalItems / pagination.limit);

  return (
    <div className="container">
      <h1>Explorador de Armaduras</h1>
      <p className="catalog-info">Total de armaduras: {totalItems}</p>
      <ArmorFilter onFilterChange={handleFilterChange} />
      {data && data.items && <ArmorGrid armors={data.items} />}
      
      {totalPages > 1 && (
        <div className="pagination">
          <button 
            onClick={() => handlePageChange(currentPage - 1)} 
            disabled={currentPage === 1}
            className="pagination-btn"
          >
            Anterior
          </button>
          <span className="pagination-info">
            Página {currentPage} de {totalPages}
          </span>
          <button 
            onClick={() => handlePageChange(currentPage + 1)} 
            disabled={currentPage === totalPages}
            className="pagination-btn"
          >
            Siguiente
          </button>
        </div>
      )}
    </div>
  );
};

export default ExploreArmorsPage;
