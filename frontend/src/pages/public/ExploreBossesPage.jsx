import React, { useState, useEffect, useCallback } from 'react';
import useFetchData from '../../hooks/useFetchData';
import { getBosses } from '../../lib/bossService';
import LoadingSpinner from '../../components/LoadingSpinner';
import BossFilter from '../../features/bosses/BossFilter';
import BossGrid from '../../features/bosses/BossGrid';

const ExploreBossesPage = () => {
  const [filters, setFilters] = useState({});
  const [pagination, setPagination] = useState({ skip: 0, limit: 20 });
  const { data, loading, error, execute } = useFetchData();

  const fetchBosses = useCallback(async () => {
    const params = { ...filters, ...pagination };
    const result = await getBosses(params);
    return result;
  }, [filters, pagination]);

  // Carga inicial de datos al montar el componente
  useEffect(() => {
    execute(fetchBosses);
  }, []);

  // Solo hace fetch cuando el usuario pulsa 'Buscar'
  const handleFilterChange = useCallback((newFilters) => {
    setFilters(newFilters);
    setPagination({ skip: 0, limit: 20 }); // Resetear paginación
    execute(async () => {
      const params = { ...newFilters, skip: 0, limit: 20 };
      return await getBosses(params);
    });
  }, [execute]);

  const handlePageChange = useCallback((newPage) => {
    const newSkip = (newPage - 1) * pagination.limit;
    setPagination(prev => ({ ...prev, skip: newSkip }));
    execute(async () => {
      const params = { ...filters, skip: newSkip, limit: pagination.limit };
      return await getBosses(params);
    });
  }, [execute, filters, pagination.limit]);

  // Aquí iría la lógica de paginación si se implementa un componente de paginación
  // const handlePageChange = (newSkip) => {
  //   setPagination(prev => ({ ...prev, skip: newSkip }));
  // };

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
      <h1>Explorador de Jefes</h1>
      <p className="catalog-info">Total de jefes: {totalItems}</p>
      <BossFilter onFilterChange={handleFilterChange} />
      {data && data.items && <BossGrid bosses={data.items} />}
      
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

export default ExploreBossesPage;
