import React, { useState, useEffect, useCallback } from 'react';
import useFetchData from '../../hooks/useFetchData';
import { getClasses } from '../../lib/classService';
import LoadingSpinner from '../../components/LoadingSpinner';
import ClassGrid from '../../features/classes/ClassGrid';

const ExploreClassesPage = () => {
  const [pagination, setPagination] = useState({ skip: 0, limit: 20 });
  const { data, loading, error, execute } = useFetchData();

  const fetchClasses = useCallback(async () => {
    const params = { ...pagination };
    const result = await getClasses(params);
    return result;
  }, [pagination]);

  useEffect(() => {
    execute(fetchClasses);
  }, [execute, fetchClasses]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <div className="container">Error: {error.message}</div>;
  }

  return (
    <div className="container">
      <h1>Explorador de Clases</h1>
      {data && data.items && <ClassGrid classes={data.items} />}
    </div>
  );
};

export default ExploreClassesPage;